#pragma once
#include "SectQuest.h"
#include "GameFramework/SaveGame.h"
#include "SectAdventure.generated.h"

UCLASS()
class XIUXIANTOWN_API USectAdventureSave : public USaveGame {
 GENERATED_BODY()
 public:
 UPROPERTY() int32 Version=1;
 UPROPERTY() int32 QuestStage=0;
 UPROPERTY() int32 Stones=0;
 UPROPERTY() int32 Wood=8;
 UPROPERTY() int32 Stone=6;
 UPROPERTY() int32 Food=6;
 UPROPERTY() int32 Renown=0;
 UPROPERTY() int32 SectLevel=1;
 UPROPERTY() TArray<FName> Herbs;
 UPROPERTY() TArray<FName> Buildings;
 UPROPERTY() TArray<int32> Jobs;
 UPROPERTY() float ProductionTime=0;
};

// Only placed in TownLayout_10. Historical maps keep their original quest director.
UCLASS()
class XIUXIANTOWN_API ASectAdventureDirector : public ASectQuestDirector {
 GENERATED_BODY()
 public:
 virtual void BeginPlay() override;
 virtual void Tick(float DeltaSeconds) override;
 virtual bool TryInteract() override;
 virtual FString GetObjectiveText() const override;
 UFUNCTION(BlueprintCallable, Category="Adventure") bool SaveProgress();
 UFUNCTION(BlueprintCallable, Category="Adventure") bool LoadProgress();
 UFUNCTION(BlueprintCallable, Category="Adventure") bool AssignJob(int32 DiscipleIndex, int32 Job);
 UFUNCTION(BlueprintPure, Category="Adventure") AActor* GetGoalActor() const;
 UFUNCTION(BlueprintPure, Category="Adventure") int32 GetCapacity() const;
 UFUNCTION(BlueprintPure, Category="Adventure") bool HasBuilding(FName Building) const;
 UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Adventure") FString SaveSlot=TEXT("Dondon_SectManagement_v1");
 UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Adventure") int32 Wood=8;
 UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Adventure") int32 Stone=6;
 UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Adventure") int32 Food=6;
 UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Adventure") int32 Renown=0;
 UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Adventure") int32 SectLevel=1;
 UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Adventure") TArray<int32> DiscipleJobs;
 UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Adventure") float ProductionTime=0;
 private:
 AActor* FindTagged(FName Tag) const;
 AActor* NearbyManagementTarget() const;
 bool InReach(AActor* Target, float Distance=260.f) const;
 bool ClearSight(AActor* Target) const;
 void Say(const FString& Text);
 void RefreshWorld();
 void Produce();
 FString PromptFor(AActor* Target) const;
 TSet<FName> Buildings;
 TMap<FName,float> GatherReady;
 FString Message;
 float MessageUntil=0;
 float AutoSaveAt=0;
 bool bJournalOpen=false;
 bool bSaveFailed=false;
 bool bLoadFailed=false;
};
