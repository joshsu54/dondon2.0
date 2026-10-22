#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "Blueprint/UserWidget.h"
#include "SectQuest.generated.h"
class UTextBlock;
UCLASS()
class XIUXIANTOWN_API USectQuestWidget : public UUserWidget {
 GENERATED_BODY()
 public:
 virtual void NativeOnInitialized() override;
 void SetQuestText(const FString& Objective, const FString& Prompt);
 private:
 UPROPERTY() TObjectPtr<UTextBlock> ObjectiveText;
 UPROPERTY() TObjectPtr<UTextBlock> PromptText;
};
UCLASS()
class XIUXIANTOWN_API ASectQuestDirector : public AActor {
 GENERATED_BODY()
 public:
 ASectQuestDirector();
 virtual void BeginPlay() override;
 virtual void Tick(float DeltaSeconds) override;
 UFUNCTION(BlueprintCallable, Category="Sect Quest") bool TryInteract();
 UFUNCTION(BlueprintPure, Category="Sect Quest") FString GetObjectiveText() const;
 UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Sect Quest") int32 QuestStage=0;
 UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Sect Quest") int32 HerbCount=0;
 UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Sect Quest") int32 SpiritStones=0;
 private:
 AActor* GetNearbyTarget() const;
 TArray<TWeakObjectPtr<AActor>> HerbActors;
 TWeakObjectPtr<AActor> Board;
 TArray<TWeakObjectPtr<AActor>> Clouds;
 TArray<FVector> CloudOrigins;
 TSet<TWeakObjectPtr<AActor>> Collected;
 UPROPERTY() TObjectPtr<USectQuestWidget> QuestWidget;
 float Elapsed=0;
};
