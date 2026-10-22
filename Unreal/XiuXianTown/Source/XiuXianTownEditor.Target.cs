using UnrealBuildTool;
public class XiuXianTownEditorTarget : TargetRules {
 public XiuXianTownEditorTarget(TargetInfo Target) : base(Target) { Type=TargetType.Editor; DefaultBuildSettings=BuildSettingsVersion.Latest; IncludeOrderVersion=EngineIncludeOrderVersion.Latest; ExtraModuleNames.Add("XiuXianTown"); }
}
