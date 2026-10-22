using UnrealBuildTool;
public class XiuXianTownTarget : TargetRules {
 public XiuXianTownTarget(TargetInfo Target) : base(Target) { Type=TargetType.Game; DefaultBuildSettings=BuildSettingsVersion.Latest; IncludeOrderVersion=EngineIncludeOrderVersion.Latest; ExtraModuleNames.Add("XiuXianTown"); }
}
