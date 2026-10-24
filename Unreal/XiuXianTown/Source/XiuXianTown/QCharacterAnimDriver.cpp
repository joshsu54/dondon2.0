#include "QCharacterAnimDriver.h"
#include "GameFramework/Character.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Animation/AnimSequenceBase.h"

UQCharacterAnimDriver::UQCharacterAnimDriver(){PrimaryComponentTick.bCanEverTick=true;PrimaryComponentTick.TickGroup=TG_PostPhysics;}

void UQCharacterAnimDriver::BeginPlay(){
 Super::BeginPlay();State.Reset();
}

void UQCharacterAnimDriver::TickComponent(float DeltaTime,ELevelTick TickType,FActorComponentTickFunction* ThisTickFunction){
 Super::TickComponent(DeltaTime,TickType,ThisTickFunction);
 auto* Character=Cast<ACharacter>(GetOwner());auto* Mesh=Character?Character->GetMesh():nullptr;if(!Mesh)return;
 const float Speed=Character->GetVelocity().Size2D();
 const bool bGrounded=!Character->GetCharacterMovement()||Character->GetCharacterMovement()->IsMovingOnGround();
 const bool bWalk=bGrounded&&Speed>MoveThreshold&&WalkAnimation;
 const FString Want=bWalk?TEXT("Walk"):TEXT("Idle");
 UAnimSequenceBase* Anim=bWalk?WalkAnimation.Get():IdleAnimation.Get();
 if(Want!=State&&Anim){Mesh->PlayAnimation(Anim,true);State=Want;}
 PlayRate=bWalk?FMath::Clamp(Speed/FMath::Max(WalkCycleSpeed,1.f),.5f,MaxWalkPlayRate):1.f;   // in the air: Idle pose, as in the template's fall
 Mesh->SetPlayRate(PlayRate);
}
