#include "SectWorkers.h"
#include "SectAdventure.h"
#include "Kismet/GameplayStatics.h"
#include "Components/SceneComponent.h"
#include "Engine/World.h"

ASectWorkers::ASectWorkers(){PrimaryActorTick.bCanEverTick=true;}
void ASectWorkers::BeginPlay(){
 Super::BeginPlay();
 Director=Cast<ASectAdventureDirector>(UGameplayStatics::GetActorOfClass(this,ASectAdventureDirector::StaticClass()));
 const FName RecruitTags[]={TEXT("SectShiDi"),TEXT("SectApplicantLin"),TEXT("SectApplicantYue")};
 for(int32 I=0;I<3;++I){
  TArray<AActor*> Found;UGameplayStatics::GetAllActorsWithTag(this,RecruitTags[I],Found);
  if(Found.IsEmpty())continue;
  auto& W=Workers[I];W.Anchor=Found[0];
  if(W.Anchor->GetRootComponent())W.Anchor->GetRootComponent()->SetMobility(EComponentMobility::Movable);
  UGameplayStatics::GetAllActorsWithTag(this,FName(*FString::Printf(TEXT("WorkerPart%d"),I)),Found);
  for(auto* A:Found){
   W.Parts.Add(A);W.Offsets.Add(A->GetActorLocation()-W.Anchor->GetActorLocation());W.Rotations.Add(A->GetActorRotation());
   if(A->GetRootComponent())A->GetRootComponent()->SetMobility(EComponentMobility::Movable);
   A->SetActorEnableCollision(false);
  }
 }
}
FVector ASectWorkers::Ground(const FVector& P)const{
 FHitResult H;FCollisionQueryParams Params;
 if(auto* Player=UGameplayStatics::GetPlayerPawn(this,0))Params.AddIgnoredActor(Player);
 for(const auto& W:Workers){if(W.Anchor.IsValid())Params.AddIgnoredActor(W.Anchor.Get());for(const auto& A:W.Parts)if(A.IsValid())Params.AddIgnoredActor(A.Get());}
 if(GetWorld()->LineTraceSingleByChannel(H,P+FVector(0,0,800),P-FVector(0,0,1000),ECC_Visibility,Params))return FVector(P.X,P.Y,H.ImpactPoint.Z+90);
 return P;
}
bool ASectWorkers::Clear(const FVector& A,const FVector& B)const{
 FHitResult H;FCollisionQueryParams Params;
 for(const auto& W:Workers){if(W.Anchor.IsValid())Params.AddIgnoredActor(W.Anchor.Get());for(const auto& P:W.Parts)if(P.IsValid())Params.AddIgnoredActor(P.Get());}
 return !GetWorld()->SweepSingleByChannel(H,A,B,FQuat::Identity,ECC_Visibility,FCollisionShape::MakeSphere(28),Params);
}
bool ASectWorkers::Plan(FWorker& W){
 W.Route.Reset();if(!W.Anchor.IsValid())return false;
 TArray<FVector> Nodes={W.Anchor->GetActorLocation(),Ground(W.Goal)};
 // A sparse camp waypoint graph. Sweeps reject blocked edges; shortest paths avoid obstacles.
 for(float X:{-1850.f,-500.f,0.f,500.f,1800.f})for(float Y:{2200.f,3000.f,3500.f,4200.f,5000.f,5500.f})Nodes.Add(Ground(FVector(X,Y,90)));
 const int32 N=Nodes.Num();TArray<float> Cost;Cost.Init(MAX_flt,N);TArray<int32> Parent;Parent.Init(INDEX_NONE,N);TArray<bool> Closed;Closed.Init(false,N);Cost[0]=0;
 for(int32 Step=0;Step<N;++Step){
  int32 U=INDEX_NONE;float Best=MAX_flt;
  for(int32 J=0;J<N;++J)if(!Closed[J]&&Cost[J]<Best){Best=Cost[J];U=J;}
  if(U==INDEX_NONE)break;if(U==1)break;Closed[U]=true;
  for(int32 V=0;V<N;++V){
   if(V==U||Closed[V])continue;const float D=FVector::Dist(Nodes[U],Nodes[V]);
   if(D>1600||Cost[U]+D>=Cost[V]||!Clear(Nodes[U],Nodes[V]))continue;
   Cost[V]=Cost[U]+D;Parent[V]=U;
  }
 }
 if(Parent[1]==INDEX_NONE)return FVector::Dist2D(Nodes[0],Nodes[1])<35;
 for(int32 At=1;At!=0;At=Parent[At]){if(At==INDEX_NONE){W.Route.Reset();return false;}W.Route.Insert(Nodes[At],0);}
 return true;
}
void ASectWorkers::Place(FWorker& W,const FVector& P,float Phase){
 W.Anchor->SetActorLocation(P);
 for(int32 J=0;J<W.Parts.Num();++J)if(auto* A=W.Parts[J].Get()){
  A->SetActorLocation(P+W.Offsets[J]+FVector(0,0,Phase*3));
  FRotator R=W.Rotations[J];R.Pitch+=Phase*4;A->SetActorRotation(R);
 }
}
void ASectWorkers::Tick(float Dt){
 Super::Tick(Dt);Clock+=Dt;if(!Director.IsValid())return;
 const FName Goals[]={TEXT("SectWood"),TEXT("SectGarden"),TEXT("SectHall")};
 for(int32 I=0;I<3;++I){
  auto& W=Workers[I];if(!W.Anchor.IsValid()||!Director->DiscipleJobs.IsValidIndex(I))continue;
  const int32 Job=Director->DiscipleJobs[I];if(Job<0||Job>2)continue;
  if(W.Job!=Job){
   W.Job=Job;TArray<AActor*> Found;UGameplayStatics::GetAllActorsWithTag(this,Goals[Job],Found);
   if(Found.IsEmpty())continue;
   W.Goal=Found[0]->GetActorLocation()+FVector((I-1)*85,-180,0);W.Retry=0;W.Route.Reset();W.State=TEXT("Traveling");
  }
  if(Director->Food<=0){W.State=TEXT("PausedNoFood");Place(W,W.Anchor->GetActorLocation(),0);continue;}
  FVector P=W.Anchor->GetActorLocation();
  if(FVector::Dist2D(P,W.Goal)<35){W.State=TEXT("Working");Place(W,Ground(P),FMath::Sin(Clock*(Job==2?1.5f:4.f)+I));continue;}
  W.Retry-=Dt;
  if(W.Route.IsEmpty()&&W.Retry<=0){Plan(W);W.Retry=2;}
  if(W.Route.IsEmpty()){W.State=TEXT("RouteBlocked");continue;}
  FVector Target=W.Route[0];const FVector Next=Ground(FMath::VInterpConstantTo(P,Target,Dt,140));
  if(!Clear(P,Next)){W.Route.Reset();W.Retry=1;W.State=TEXT("RouteBlocked");continue;}
  W.State=TEXT("Traveling");Place(W,Next,.2f*FMath::Sin(Clock*8));
  if(FVector::Dist2D(Next,Target)<20)W.Route.RemoveAt(0);
 }
}
FString ASectWorkers::GetWorkerState(int32 I)const{return I>=0&&I<3?Workers[I].State:TEXT("Invalid");}
FVector ASectWorkers::GetWorkerLocation(int32 I)const{return I>=0&&I<3&&Workers[I].Anchor.IsValid()?Workers[I].Anchor->GetActorLocation():FVector::ZeroVector;}
