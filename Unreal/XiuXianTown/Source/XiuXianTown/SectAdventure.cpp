#include "SectAdventure.h"
#include "Kismet/GameplayStatics.h"
#include "GameFramework/Pawn.h"
#include "GameFramework/PlayerController.h"
#include "InputCoreTypes.h"
#include "DrawDebugHelpers.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"

namespace {
 const FName FacilityTags[]={TEXT("SectGarden"),TEXT("SectDorm"),TEXT("SectHall")};
 const FName RecruitTags[]={TEXT("SectShiDi"),TEXT("SectApplicantLin"),TEXT("SectApplicantYue")};
 const TCHAR* Names[]={TEXT("石砥"),TEXT("林溪"),TEXT("岳青")};
 const TCHAR* Jobs[]={TEXT("採集木石"),TEXT("照料藥圃"),TEXT("修煉傳道")};
 constexpr float WorkPeriod=20.f;
}

AActor* ASectAdventureDirector::FindTagged(FName Tag) const {
 TArray<AActor*> Found; UGameplayStatics::GetAllActorsWithTag(this,Tag,Found);
 return Found.IsEmpty()?nullptr:Found[0];
}
bool ASectAdventureDirector::ClearSight(AActor* Target) const {
 auto* Pawn=UGameplayStatics::GetPlayerPawn(this,0); if (!Pawn || !Target) return false;
 FHitResult Hit; FCollisionQueryParams Params; Params.AddIgnoredActor(Pawn); Params.AddIgnoredActor(Target);
 // Herb pivots sit at ground level; aim above the pivot so raised paving does not occlude interaction.
 return !GetWorld()->LineTraceSingleByChannel(Hit,Pawn->GetActorLocation(),Target->GetActorLocation()+FVector(0,0,60),ECC_Visibility,Params);
}
bool ASectAdventureDirector::InReach(AActor* Target,float Distance) const {
 auto* Pawn=UGameplayStatics::GetPlayerPawn(this,0);
 return Pawn && Target && FVector::Dist(Pawn->GetActorLocation(),Target->GetActorLocation())<Distance && ClearSight(Target);
}
bool ASectAdventureDirector::HasBuilding(FName Building) const { return Buildings.Contains(Building); }
int32 ASectAdventureDirector::GetCapacity() const { return HasBuilding("SectDorm")?4:1; }
void ASectAdventureDirector::Say(const FString& Text) { Message=Text; MessageUntil=Elapsed+6.f; }

void ASectAdventureDirector::BeginPlay() {
 Super::BeginPlay();
 FParse::Value(FCommandLine::Get(),TEXT("SectSaveSlot="),SaveSlot);
 LoadProgress(); RefreshWorld(); AutoSaveAt=Elapsed+30;
 if (QuestWidget) QuestWidget->SetManagementMode(false);
 Say(TEXT("凌雲宗百廢待興。先完成採藥委託，帶石砥一起重建宗門。"));
}

AActor* ASectAdventureDirector::NearbyManagementTarget() const {
 TArray<AActor*> Found; UGameplayStatics::GetAllActorsWithTag(this,"SectInteract",Found);
 auto* Pawn=UGameplayStatics::GetPlayerPawn(this,0); if (!Pawn) return nullptr;
 AActor* Best=nullptr; float Distance=260;
 for (auto* Actor:Found) {
  const float D=FVector::Dist(Pawn->GetActorLocation(),Actor->GetActorLocation());
  if (D<Distance && ClearSight(Actor)) { Best=Actor; Distance=D; }
 }
 return Best;
}

bool ASectAdventureDirector::AssignJob(int32 DiscipleIndex,int32 Job) {
 if (!DiscipleJobs.IsValidIndex(DiscipleIndex) || Job<0 || Job>2) return false;
 if ((Job==1 && !HasBuilding("SectGarden")) || (Job==2 && !HasBuilding("SectHall"))) {
  Say(TEXT("先興建對應設施，才能安排這項工作。")); return false;
 }
 DiscipleJobs[DiscipleIndex]=Job;
 Say(FString::Printf(TEXT("%s已改派：%s。"),Names[DiscipleIndex],Jobs[Job]));
 SaveProgress(); return true;
}

bool ASectAdventureDirector::TryInteract() {
 if (auto* Target=NearbyManagementTarget()) {
  if (QuestStage<3) { Say(TEXT("先到北端委託牌完成採藥，取得重建宗門的信任與資金。")); return false; }
  for (int32 I=0;I<3;++I) if (Target->ActorHasTag(RecruitTags[I])) {
   if (DiscipleJobs.IsValidIndex(I)) {
    int32 Job=(DiscipleJobs[I]+1)%3;
    for (int32 N=0;N<3;++N) {
     if ((Job==0) || (Job==1 && HasBuilding("SectGarden")) || (Job==2 && HasBuilding("SectHall"))) return AssignJob(I,Job);
     Job=(Job+1)%3;
    }
   }
   if (I!=DiscipleJobs.Num()) { Say(TEXT("先邀請前一位弟子入門：石砥 → 林溪 → 岳青。")); return false; }
   if (DiscipleJobs.Num()>=GetCapacity()) { Say(TEXT("住處不足，請先興建弟子舍，床位會提升到 4。")); return false; }
   const int32 Cost=I==0?0:I==1?5:8; const int32 Meals=I==0?0:I==1?2:3;
   if (SpiritStones<Cost || Food<Meals) { Say(TEXT("招募資源不足；可採野果，或到委託牌交付木石賺靈石。")); return false; }
   SpiritStones-=Cost; Food-=Meals; DiscipleJobs.Add(0); Renown+=3;
   Say(I==0?TEXT("石砥：我沒有什麼天分，但我每天都會來。第一位弟子加入！"):
       FString::Printf(TEXT("%s加入凌雲宗！按 J 查看工作分派。"),Names[I]));
   RefreshWorld(); SaveProgress(); return true;
  }
  for (int32 I=0;I<3;++I) if (Target->ActorHasTag(FacilityTags[I])) {
   if (HasBuilding(FacilityTags[I])) {
    if (I==0 && !DiscipleJobs.IsEmpty()) return AssignJob(0,1);
    Say(I==1?TEXT("弟子舍：四個床位。可前往招募新的弟子。"):
        TEXT("靜修臺已開放。按 J，再按弟子編號切換為修煉傳道。")); return false;
   }
   const int32 W[]={6,12,8}, S[]={4,8,6}, Money[]={0,6,8};
   if (DiscipleJobs.IsEmpty()) { Say(TEXT("先邀請石砥，一起動手重建宗門。")); return false; }
   if (Wood<W[I] || Stone<S[I] || SpiritStones<Money[I]) { Say(TEXT("材料不足。南側竹林與採石點可採集；委託牌可用木石換靈石。")); return false; }
   Wood-=W[I]; Stone-=S[I]; SpiritStones-=Money[I]; Buildings.Add(FacilityTags[I]); Renown+=5;
   if (I==0) DiscipleJobs[0]=1;
   Say(I==0?TEXT("藥圃修復！石砥開始照料，每輪消耗 1 糧食、產出 4 糧食。"):
       I==1?TEXT("弟子舍完工！床位提升至 4，可招募林溪與岳青。"):
       TEXT("靜修臺完工！弟子可修煉傳道，累積宗門聲望。"));
   RefreshWorld(); SaveProgress(); return true;
  }
  for (const FName Resource:{FName("SectWood"),FName("SectStone"),FName("SectFood")}) if (Target->ActorHasTag(Resource)) {
   if (GatherReady.FindRef(Resource)>Elapsed) { Say(TEXT("這處資源正在恢復，稍等幾秒。")); return false; }
   GatherReady.Add(Resource,Elapsed+6.f);
   if (Resource=="SectWood") Wood=FMath::Min(999,Wood+4);
   else if (Resource=="SectStone") Stone=FMath::Min(999,Stone+3);
   else Food=FMath::Min(999,Food+4);
   Say(TEXT("採集完成，材料已收入宗門庫房。")); SaveProgress(); return true;
  }
  if (Target->ActorHasTag("SectMaster")) {
   if (SectLevel>=2) { Say(TEXT("雲不鶴：這山門總算又有人氣了。繼續照顧好這些孩子。")); return false; }
   if (DiscipleJobs.Num()<3 || Buildings.Num()<3 || Renown<30 || SpiritStones<15) {
    Say(TEXT("振興條件：3 位弟子、3 座設施、聲望 30、靈石 15。")); return false;
   }
   SpiritStones-=15; SectLevel=2;
   Say(TEXT("凌雲宗晉升二品！首輪重建完成；可以繼續經營、分工與接取委託。")); SaveProgress(); return true;
  }
 }
 if (QuestStage==3 && InReach(Board.Get(),250)) {
  if (Wood<4 || Stone<2) { Say(TEXT("小鎮建材委託需要木材 4、石料 2，獎勵 6 靈石與 2 聲望。")); return false; }
  Wood-=4; Stone-=2; SpiritStones=FMath::Min(999,SpiritStones+6); Renown=FMath::Min(999,Renown+2);
  Say(TEXT("建材委託完成：靈石 +6，聲望 +2。可以重複承接。")); SaveProgress(); return true;
 }
 // Keep the original three-herb quest and its range checks; add visibility protection.
 auto* Target=GetNearbyTarget(); if (!Target || !ClearSight(Target)) return false;
 const bool Changed=Super::TryInteract();
 if (Changed) { if (QuestStage==3) Say(TEXT("獲得 10 靈石！回到小鎮南方的重建營地，邀請石砥。")); SaveProgress(); }
 return Changed;
}

void ASectAdventureDirector::Produce() {
 if (DiscipleJobs.IsEmpty()) return;
 bool Worked=false;
 // Gardeners work first so one productive garden can feed the whole starting sect.
 for (const int32 Job:{1,0,2}) for (const int32 Assigned:DiscipleJobs) if (Assigned==Job && Food>0) {
  if ((Job==1 && !HasBuilding("SectGarden")) || (Job==2 && !HasBuilding("SectHall"))) continue;
  --Food; Worked=true;
  if (Job==0) { Wood=FMath::Min(999,Wood+4); Stone=FMath::Min(999,Stone+3); }
  else if (Job==1) Food=FMath::Min(999,Food+4);
  else Renown=FMath::Min(999,Renown+3);
 }
 if (!Worked) Say(TEXT("糧食不足，弟子暫停工作。去採野果，並安排一位弟子照料藥圃。"));
 SaveProgress();
}

void ASectAdventureDirector::RefreshWorld() {
 for (const FName Tag:FacilityTags) {
  TArray<AActor*> Found; const FName BuiltTag(*(Tag.ToString()+TEXT("Built")));
  UGameplayStatics::GetAllActorsWithTag(this,BuiltTag,Found);
  for (auto* Actor:Found) { Actor->SetActorHiddenInGame(!HasBuilding(Tag)); Actor->SetActorEnableCollision(false); }
 }
 for (const auto& Herb:HerbActors) if (Herb.IsValid()) {
  const bool Hidden=Collected.Contains(Herb); Herb->SetActorHiddenInGame(Hidden); Herb->SetActorEnableCollision(false);
 }
}

bool ASectAdventureDirector::SaveProgress() {
 // Never replace an unreadable existing checkpoint with a fresh game.
 if (bLoadFailed) return false;
 auto* Save=Cast<USectAdventureSave>(UGameplayStatics::CreateSaveGameObject(USectAdventureSave::StaticClass()));
 if (!Save) { bSaveFailed=true; return false; }
 Save->QuestStage=QuestStage; Save->Stones=SpiritStones; Save->Wood=Wood; Save->Stone=Stone; Save->Food=Food;
 Save->Renown=Renown; Save->SectLevel=SectLevel; Save->Jobs=DiscipleJobs; Save->ProductionTime=ProductionTime;
 for (const auto& Herb:Collected) if (Herb.IsValid()) Save->Herbs.Add(Herb->GetFName());
 Save->Buildings=Buildings.Array();
 bSaveFailed=!UGameplayStatics::SaveGameToSlot(Save,SaveSlot,0); return !bSaveFailed;
}
bool ASectAdventureDirector::LoadProgress() {
 if (!UGameplayStatics::DoesSaveGameExist(SaveSlot,0)) return false;
 auto* Save=Cast<USectAdventureSave>(UGameplayStatics::LoadGameFromSlot(SaveSlot,0));
 if (!Save || Save->Version!=1 || Save->QuestStage<0 || Save->QuestStage>3 || Save->Jobs.Num()>3) {
  bSaveFailed=true; bLoadFailed=true; Say(TEXT("存檔無法讀取；已保留原檔並暫停自動存檔。")); return false;
 }
 QuestStage=Save->QuestStage; SpiritStones=FMath::Clamp(Save->Stones,0,999);
 Wood=FMath::Clamp(Save->Wood,0,999); Stone=FMath::Clamp(Save->Stone,0,999); Food=FMath::Clamp(Save->Food,0,999);
 Renown=FMath::Clamp(Save->Renown,0,999); SectLevel=FMath::Clamp(Save->SectLevel,1,2);
 Buildings.Reset(); for (const FName Tag:FacilityTags) if (Save->Buildings.Contains(Tag)) Buildings.Add(Tag);
 DiscipleJobs=Save->Jobs; for (int32& Job:DiscipleJobs) {
  if (Job<0 || Job>2 || (Job==1 && !HasBuilding("SectGarden")) || (Job==2 && !HasBuilding("SectHall"))) Job=0;
 }
 ProductionTime=FMath::IsFinite(Save->ProductionTime)?FMath::Clamp(Save->ProductionTime,0.f,WorkPeriod):0.f;
 Collected.Reset(); for (const auto& Herb:HerbActors) if (Herb.IsValid() && Save->Herbs.Contains(Herb->GetFName())) Collected.Add(Herb);
 HerbCount=Collected.Num(); RefreshWorld(); bSaveFailed=false; bLoadFailed=false; return true;
}

AActor* ASectAdventureDirector::GetGoalActor() const {
 if (QuestStage==0 || QuestStage==2) return Board.Get();
 if (QuestStage==1) {
  AActor* Best=nullptr; double Distance=1.e20; auto* Pawn=UGameplayStatics::GetPlayerPawn(this,0);
  for (const auto& Herb:HerbActors) if (Herb.IsValid() && !Collected.Contains(Herb)) {
   const double D=Pawn?FVector::DistSquared(Pawn->GetActorLocation(),Herb->GetActorLocation()):0;
   if (D<Distance) { Best=Herb.Get(); Distance=D; }
  } return Best;
 }
 if (DiscipleJobs.IsEmpty()) return FindTagged("SectShiDi");
 if (Food==0) return FindTagged("SectFood");
 if (!HasBuilding("SectGarden")) return FindTagged("SectGarden");
 if (!HasBuilding("SectDorm")) return FindTagged("SectDorm");
 if (DiscipleJobs.Num()<2) return FindTagged("SectApplicantLin");
 if (!HasBuilding("SectHall")) return FindTagged("SectHall");
 if (DiscipleJobs.Num()<3) return FindTagged("SectApplicantYue");
 return FindTagged("SectMaster");
}

FString ASectAdventureDirector::GetObjectiveText() const {
 FString Goal;
 if (QuestStage<3) Goal=Super::GetObjectiveText();
 else if (SectLevel==2) Goal=TEXT("首輪重建完成！持續經營宗門，安排弟子生產。 ");
 else if (DiscipleJobs.IsEmpty()) Goal=TEXT("去南側重建營地邀請石砥，開始經營宗門。");
 else if (Food==0) Goal=TEXT("糧食用盡！去野果叢採集，並安排藥圃工作。");
 else if (!HasBuilding("SectGarden")) Goal=TEXT("修復藥圃：木材 6、石料 4；石砥會自動照料。");
 else if (!HasBuilding("SectDorm")) Goal=TEXT("興建弟子舍：木材 12、石料 8、靈石 6。");
 else if (DiscipleJobs.Num()<2) Goal=TEXT("邀請林溪：靈石 5、糧食 2；加入後可採集木石。");
 else if (!HasBuilding("SectHall")) Goal=TEXT("興建靜修臺：木材 8、石料 6、靈石 8。");
 else if (DiscipleJobs.Num()<3) Goal=TEXT("邀請岳青：靈石 8、糧食 3；按 J 安排分工。");
 else Goal=TEXT("向雲不鶴申請晉升：3 位弟子、3 座設施、聲望 30、靈石 15。");
 FString Result=FString::Printf(TEXT("宗門 %d 品  ·  弟子 %d / %d  ·  聲望 %d\n木材 %d  石料 %d  糧食 %d  靈石 %d\n%s\n"),
  SectLevel,DiscipleJobs.Num(),GetCapacity(),Renown,Wood,Stone,Food,SpiritStones,*Goal);
 auto* Pawn=UGameplayStatics::GetPlayerPawn(this,0);
 if (auto* Target=GetGoalActor(); Target && Pawn) {
  const FVector Delta=Target->GetActorLocation()-Pawn->GetActorLocation();
  Result+=FString::Printf(TEXT("青玉光柱：目標距離 %.0f 公尺。\n"),Delta.Size()/100.f);
 }
 if (!DiscipleJobs.IsEmpty()) Result+=FString::Printf(TEXT("下一輪工作：%d 秒（每位弟子消耗 1 糧食）\n"),FMath::CeilToInt(WorkPeriod-ProductionTime));
 if (bJournalOpen) {
  Result+=TEXT("\n宗門簿｜按 1 / 2 / 3 切換對應弟子的工作\n");
  for (int32 I=0;I<DiscipleJobs.Num();++I) Result+=FString::Printf(TEXT("%d  %s：%s\n"),I+1,Names[I],Jobs[DiscipleJobs[I]]);
  Result+=TEXT("採集：木材 +4、石料 +3\n藥圃：糧食 +4；靜修：聲望 +3\n南側：重建營地、林溪、岳青與採集點\n北側：委託牌、三株靈草與山門\n建材委託：木 4 + 石 2 → 靈石 6、聲望 2\n資源每處 6 秒恢復；離線不生產。\n");
 }
 return Result;
}

FString ASectAdventureDirector::PromptFor(AActor* Target) const {
 if (!Target) return TEXT("WASD 移動 · 空白跳躍 · E 互動 · J 宗門簿 · F5 存檔");
 for (int32 I=0;I<3;++I) if (Target->ActorHasTag(RecruitTags[I])) {
  if (DiscipleJobs.IsValidIndex(I)) return FString::Printf(TEXT("E 與%s談話／切換工作（目前：%s）"),Names[I],Jobs[DiscipleJobs[I]]);
  return FString::Printf(TEXT("E 招募%s｜%d 靈石、%d 糧食"),Names[I],I==0?0:I==1?5:8,I==0?0:I==1?2:3);
 }
 if (Target->ActorHasTag("SectGarden")) return HasBuilding("SectGarden")?TEXT("E 安排石砥照料藥圃"):TEXT("E 修復藥圃｜木 6、石 4");
 if (Target->ActorHasTag("SectDorm")) return HasBuilding("SectDorm")?TEXT("弟子舍已完工，床位 4"):TEXT("E 興建弟子舍｜木 12、石 8、靈石 6");
 if (Target->ActorHasTag("SectHall")) return HasBuilding("SectHall")?TEXT("J 開啟宗門簿，分派修煉工作"):TEXT("E 興建靜修臺｜木 8、石 6、靈石 8");
 if (Target->ActorHasTag("SectWood")) return TEXT("E 採竹木 +4（6 秒恢復）");
 if (Target->ActorHasTag("SectStone")) return TEXT("E 採石料 +3（6 秒恢復）");
 if (Target->ActorHasTag("SectFood")) return TEXT("E 採野果 +4（6 秒恢復）");
 if (Target->ActorHasTag("SectMaster")) return TEXT("E 與雲不鶴談話／申請宗門晉升");
 return TEXT("E 互動");
}

void ASectAdventureDirector::Tick(float DeltaSeconds) {
 Super::Tick(DeltaSeconds); // Cloud drift and E dispatch use virtual TryInteract().
 if (auto* PC=UGameplayStatics::GetPlayerController(this,0)) {
  if (PC->WasInputKeyJustPressed(EKeys::J)) { bJournalOpen=!bJournalOpen; if (QuestWidget) QuestWidget->SetManagementMode(bJournalOpen); }
  if (PC->WasInputKeyJustPressed(EKeys::F5)) { if (SaveProgress()) Say(TEXT("宗門進度已保存。")); }
  const FKey Keys[]={EKeys::One,EKeys::Two,EKeys::Three};
  if (bJournalOpen) for (int32 I=0;I<DiscipleJobs.Num();++I) if (PC->WasInputKeyJustPressed(Keys[I])) {
   int32 Job=(DiscipleJobs[I]+1)%3;
   for (int32 N=0;N<3;++N) {
    if (Job==0 || (Job==1 && HasBuilding("SectGarden")) || (Job==2 && HasBuilding("SectHall"))) { AssignJob(I,Job); break; }
    Job=(Job+1)%3;
   }
  }
 }
 if (!DiscipleJobs.IsEmpty()) {
  ProductionTime+=DeltaSeconds;
  while (ProductionTime>=WorkPeriod) { ProductionTime-=WorkPeriod; Produce(); }
 }
 if (Elapsed>=AutoSaveAt) { SaveProgress(); AutoSaveAt=Elapsed+30; }
 if (auto* Goal=GetGoalActor()) {
  const FVector P=Goal->GetActorLocation();
  DrawDebugLine(GetWorld(),P+FVector(0,0,100),P+FVector(0,0,500),FColor(90,240,195),false,-1,0,5);
  DrawDebugSphere(GetWorld(),P+FVector(0,0,500),28,12,FColor(90,240,195),false,-1,0,2);
 }
 FString Prompt=PromptFor(NearbyManagementTarget());
 if (!NearbyManagementTarget()) if (auto* Target=GetNearbyTarget()) {
  if (Target!=Board.Get()) Prompt=TEXT("E 採集靈草");
  else Prompt=QuestStage==0?TEXT("E 接取採藥委託"):QuestStage==2?TEXT("E 交付三株靈草，獲得 10 靈石"):
   QuestStage==3?TEXT("E 交付建材｜木 4、石 2 → 靈石 6、聲望 2"):TEXT("先採齊三株靈草，再回來交付。");
 }
 if (MessageUntil>Elapsed) Prompt=Message+TEXT("\n")+Prompt;
 if (bLoadFailed) Prompt+=TEXT("\n原存檔無法讀取，已保留原檔並暫停儲存。");
 else if (bSaveFailed) Prompt+=TEXT("\n存檔失敗，請檢查磁碟權限並按 F5 重試。");
 if (QuestWidget) QuestWidget->SetQuestText(GetObjectiveText(),Prompt);
}
