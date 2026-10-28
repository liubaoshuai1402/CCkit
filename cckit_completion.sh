# CCkit Bash 补全脚本
# CCkit 功能说明：为 cckit 命令及 tools.json 中的功能名提供命令补全。
# 使用方法: source /path/to/cckit_completion.sh

_cckit_completions() {
    local cur prev cmds
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"

    # 第一个单词，补全命令名
    if [[ $COMP_CWORD == 0 ]]; then
        COMPREPLY=( $(compgen -W "cckit" -- "$cur") )
        return 0
    fi

    # 第二个单词，补全功能函数
    if [[ $COMP_CWORD == 1 ]]; then
        if command -v cckit >/dev/null 2>&1; then
            cmds=$(cckit --listall 2>/dev/null | sed -n 's/^- \([^:]*\):.*/\1/p')
            COMPREPLY=( $(compgen -W "$cmds" -- "$cur") )
        fi
        return 0
    fi
}

# 注册补全函数，大小写必须和实际文件名一致
complete -o default -F _cckit_completions cckit
