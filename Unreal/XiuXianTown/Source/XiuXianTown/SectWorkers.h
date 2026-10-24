#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "SectWorkers.generated.h"

// Local camp navigation for the existing blockout disciples. No asset or save migration.
UCLASS()
class XIUXIANTOWN_API ASectWorkers : public AActor {
 GENERATED_BODY()
 public:
 ASectWorkers();
 virtual void BeginPlay() override;
 virtual void Tick(float DeltaSeconds) override;
 UFUNCTION(BlueprintPure,Category="SectWorkers") FString GetWorkerState(int32 Index) const;
 UFUNCTION(BlueprintPure,Category="SectWorkers") FVector GetWorkerLocation(int32 Index) const;
 private:
 struct FWorker {
  TWeakObjectPtr<AActor> Anchor;
  TArray<TWeakObjectPtr<AActor>> Parts;
  TArray<FVector> Offsets;
  TArray<FRotator> Rotations;
  TArray<FVector> Route;
  int32 Job=-1;
  FString State=TEXT("WaitingRecruitment");
  FVector Goal=FVector::ZeroVector;
  float Retry=0;
 };
 FWorker Workers[3];
 TWeakObjectPtr<class ASectAdventureDirector> Director;
 FVector Ground(const FVector& Position) const;
 bool Clear(const FVector& A,const FVector& B) const;
 bool Plan(FWorker& Worker);
 void Place(FWorker& Worker,const FVector& Position,float WorkPhase);
 float Clock=0;
};
