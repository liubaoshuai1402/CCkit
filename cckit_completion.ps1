# CCkit PowerShell 补全脚本
# 功能说明：为 cckit 命令提供 tools.json 中函数名的补全，与 Linux 的
#           cckit_completion.sh 对应。
# 使用方法：在 PowerShell 中执行
#   . "D:\path\to\cckit_completion.ps1"
# 或把该行加入 $PROFILE，使每次启动 PowerShell 自动生效：
#   Add-Content -Path $PROFILE -Value '. "D:\path\to\cckit_completion.ps1"'
# 若执行策略禁止加载脚本，请先执行：
#   Set-ExecutionPolicy -Scope CurrentUser RemoteSigned

$__cckitToolsJson = Join-Path $PSScriptRoot "tools.json"

if (-not (Test-Path -LiteralPath $__cckitToolsJson)) {
    Write-Warning "cckit completion: tools.json not found at '$__cckitToolsJson'"
    return
}

# 补全器主体：用占位符 __CCKIT_TOOLS_JSON__ 代替路径，加载时再替换成实际
# 绝对路径，避免脚本块在部分 PowerShell 版本中看不到外层变量的情况。
$__cckitCompleterBody = @'
param($wordToComplete, $commandAst, $cursorPosition)

$tools = Get-Content -LiteralPath '__CCKIT_TOOLS_JSON__' -Raw | ConvertFrom-Json

$tools.PSObject.Properties |
    Where-Object { $_.Name -like "$wordToComplete*" } |
    Sort-Object Name |
    ForEach-Object {
        [System.Management.Automation.CompletionResult]::new(
            $_.Name,
            $_.Name,
            "ParameterValue",
            "cckit: $($_.Value.desc)"
        )
    }
'@
$__cckitCompleterSource = $__cckitCompleterBody.Replace("__CCKIT_TOOLS_JSON__", $__cckitToolsJson)
$__cckitCompleter = [scriptblock]::Create($__cckitCompleterSource)

# -Native：针对外部命令（cckit.bat）的补全器。
# PowerShell 按位置传入 $wordToComplete、$commandAst、$cursorPosition，
# 与普通 PowerShell 命令的 5 个参数不同。
Register-ArgumentCompleter -Native -CommandName cckit, cckit.bat -ScriptBlock $__cckitCompleter
