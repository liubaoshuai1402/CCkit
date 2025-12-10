# CCkit Bash/Zsh 补全脚本
# 使用方法: source /path/to/CCkit_completion.sh

_CCkit_completions() {
    local cur prev cmds
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"

    # 第一个单词，补全命令名
    if [[ $COMP_CWORD == 0 ]]; then
        COMPREPLY=( $(compgen -W "CCkit" -- "$cur") )
        return 0
    fi

    # 第二个单词，补全功能函数
    if [[ $COMP_CWORD == 1 ]]; then
        if command -v CCkit >/dev/null 2>&1; then
            cmds=$(CCkit --listall 2>/dev/null)
            COMPREPLY=( $(compgen -W "$cmds" -- "$cur") )
        fi
        return 0
    fi
}

# 注册补全函数，大小写必须和实际文件名一致
complete -F _CCkit_completions CCkit