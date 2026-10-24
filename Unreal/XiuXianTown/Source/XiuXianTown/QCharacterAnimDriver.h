#pragma once
#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "QCharacterAnimDriver.generated.h"

// Plays the QCharacters17 v005 Idle/Walk loops on the owning character's mesh (single-node mode, no Animation Blueprint).
// Walk plays faster with ground speed so the steps keep pace with the capsule.
UCLASS(ClassGroup=(Animation),meta=(BlueprintSpawnableComponent))
class XIUXIANTOWN_API UQCharacterAnimDriver : public UActorComponent {
 GENERATED_BODY()
 public:
 UQCharacterAnimDriver();
 virtual void BeginPlay() override;
 virtual void TickComponent(float DeltaTime,ELevelTick TickType,FActorComponentTickFunction* ThisTickFunction) override;
 UPROPERTY(EditAnywhere,BlueprintReadWrite,Category="QCharacter") TObjectPtr<class UAnimSequenceBase> IdleAnimation;
 UPROPERTY(EditAnywhere,BlueprintReadWrite,Category="QCharacter") TObjectPtr<class UAnimSequenceBase> WalkAnimation;
 // Ground speed (cm/s) the Walk loop matches at play rate 1: two 30 cm steps per second.
 UPROPERTY(EditAnywhere,BlueprintReadWrite,Category="QCharacter") float WalkCycleSpeed=60.f;
 UPROPERTY(EditAnywhere,BlueprintReadWrite,Category="QCharacter") float MoveThreshold=8.f;
 UPROPERTY(EditAnywhere,BlueprintReadWrite,Category="QCharacter") float MaxWalkPlayRate=3.4f;
 UFUNCTION(BlueprintPure,Category="QCharacter") FString GetAnimState() const {return State;}
 UFUNCTION(BlueprintPure,Category="QCharacter") float GetPlayRate() const {return PlayRate;}
 private:
 FString State;
 float PlayRate=1.f;
};
