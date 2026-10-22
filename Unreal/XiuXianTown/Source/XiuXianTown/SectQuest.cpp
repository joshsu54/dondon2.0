#include "SectQuest.h"
#include "Blueprint/WidgetTree.h"
#include "Components/Border.h"
#include "Components/CanvasPanel.h"
#include "Components/CanvasPanelSlot.h"
#include "Components/VerticalBox.h"
#include "Components/TextBlock.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/Pawn.h"
#include "Kismet/GameplayStatics.h"
#include "InputCoreTypes.h"
#include "Styling/CoreStyle.h"

void USectQuestWidget::NativeOnInitialized() {
 Super::NativeOnInitialized();
 if (ObjectiveText) return;
 auto* Canvas=WidgetTree->ConstructWidget<UCanvasPanel>();
 WidgetTree->RootWidget=Canvas;
 auto* Border=WidgetTree->ConstructWidget<UBorder>();
 Border->SetBrushColor(FLinearColor(.025f,.055f,.05f,.92f));
 Border->SetPadding(FMargin(18));
 auto* Slot=Canvas->AddChildToCanvas(Border);
 Slot->SetPosition(FVector2D(24,24)); Slot->SetSize(FVector2D(530,175));
 auto* Box=WidgetTree->ConstructWidget<UVerticalBox>(); Border->SetContent(Box);
 auto* Title=WidgetTree->ConstructWidget<UTextBlock>();
 Title->SetFont(FCoreStyle::GetDefaultFontStyle("Bold",24));
 Title->SetText(FText::FromString(TEXT("宗門委託 · 初入山門")));
 Title->SetColorAndOpacity(FSlateColor(FLinearColor(.65f,.9f,.78f)));
 Box->AddChildToVerticalBox(Title);
 ObjectiveText=WidgetTree->ConstructWidget<UTextBlock>();
 ObjectiveText->SetFont(FCoreStyle::GetDefaultFontStyle("Regular",20));
 ObjectiveText->SetAutoWrapText(true); Box->AddChildToVerticalBox(ObjectiveText);
 PromptText=WidgetTree->ConstructWidget<UTextBlock>();
 PromptText->SetFont(FCoreStyle::GetDefaultFontStyle("Regular",18));
 PromptText->SetColorAndOpacity(FSlateColor(FLinearColor(1,.82f,.4f)));
 PromptText->SetAutoWrapText(true); Box->AddChildToVerticalBox(PromptText);
}
void USectQuestWidget::SetQuestText(const FString& Objective,const FString& Prompt) {
 if (ObjectiveText) ObjectiveText->SetText(FText::FromString(Objective));
 if (PromptText) PromptText->SetText(FText::FromString(Prompt));
}
ASectQuestDirector::ASectQuestDirector() { PrimaryActorTick.bCanEverTick=true; }
void ASectQuestDirector::BeginPlay() {
 Super::BeginPlay();
 TArray<AActor*> Found;
 UGameplayStatics::GetAllActorsWithTag(this,"QuestBoard",Found);
 if (!Found.IsEmpty()) Board=Found[0];
 Found.Reset(); UGameplayStatics::GetAllActorsWithTag(this,"QuestHerb",Found);
 for (auto* A:Found) HerbActors.Add(A);
 Found.Reset(); UGameplayStatics::GetAllActorsWithTag(this,"DriftCloud",Found);
 for (auto* A:Found) { Clouds.Add(A); CloudOrigins.Add(A->GetActorLocation()); }
 if (auto* PC=UGameplayStatics::GetPlayerController(this,0)) {
  QuestWidget=CreateWidget<USectQuestWidget>(PC,USectQuestWidget::StaticClass());
  if (QuestWidget) QuestWidget->AddToViewport();
 }
}
AActor* ASectQuestDirector::GetNearbyTarget() const {
 auto* Pawn=UGameplayStatics::GetPlayerPawn(this,0); if (!Pawn) return nullptr;
 const FVector Location=Pawn->GetActorLocation();
 // The board remains interactive so an early return cannot grant a reward.
 if (Board.IsValid() && FVector::Dist(Location,Board->GetActorLocation())<250) return Board.Get();
 AActor* Nearest=nullptr; float Best=220;
 if (QuestStage==1) for (const auto& Herb:HerbActors) {
  if (!Herb.IsValid() || Collected.Contains(Herb)) continue;
  const float D=FVector::Dist(Location,Herb->GetActorLocation());
  if (D<Best) { Best=D; Nearest=Herb.Get(); }
 }
 return Nearest;
}
bool ASectQuestDirector::TryInteract() {
 auto* Target=GetNearbyTarget(); if (!Target) return false;
 if (Target==Board.Get()) {
  if (QuestStage==0) { QuestStage=1; return true; }
  if (QuestStage==2 && HerbCount==3) { QuestStage=3; SpiritStones+=10; return true; }
  return false;
 }
 if (QuestStage!=1 || Collected.Contains(Target)) return false;
 Collected.Add(Target); HerbCount++;
 Target->SetActorHiddenInGame(true); Target->SetActorEnableCollision(false);
 if (HerbCount==3) QuestStage=2;
 return true;
}
FString ASectQuestDirector::GetObjectiveText() const {
 if (QuestStage==0) return TEXT("前往小鎮北端的委託牌，接取採藥任務。");
 if (QuestStage==1) return FString::Printf(TEXT("沿青石路前往山門，採集靈草 %d / 3。"),HerbCount);
 if (QuestStage==2) return TEXT("靈草已齊！返回小鎮委託牌領取獎勵。");
 return FString::Printf(TEXT("委託完成！獲得 10 靈石。持有靈石：%d"),SpiritStones);
}
void ASectQuestDirector::Tick(float DeltaSeconds) {
 Super::Tick(DeltaSeconds); Elapsed+=DeltaSeconds;
 for (int32 I=0;I<Clouds.Num();++I) if (Clouds[I].IsValid()) {
  const float Phase=I*1.7f;
  Clouds[I]->SetActorLocation(CloudOrigins[I]+FVector(FMath::Sin(Elapsed*.035f+Phase)*180, FMath::Cos(Elapsed*.025f+Phase)*100,FMath::Sin(Elapsed*.04f+Phase)*25));
 }
 if (auto* PC=UGameplayStatics::GetPlayerController(this,0))
  if (PC->WasInputKeyJustPressed(EKeys::E)) TryInteract();
 FString Prompt=TEXT("WASD 移動 · 滑鼠轉向 · 空白鍵跳躍");
 if (auto* Target=GetNearbyTarget()) {
  if (Target==Board.Get()) Prompt=QuestStage==0?TEXT("按 E 接取委託"):QuestStage==2?TEXT("按 E 交付靈草，領取 10 靈石"):QuestStage==3?TEXT("委託已完成，謝謝你的幫忙！"):TEXT("尚未採齊三株靈草，沿北側青石路尋找。");
  else Prompt=TEXT("按 E 採集靈草");
 }
 if (QuestWidget) QuestWidget->SetQuestText(GetObjectiveText(),Prompt);
}
