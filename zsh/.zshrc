# Enable Powerlevel10k instant prompt. Should stay close to the top of ~/.zshrc.
if [[ -r "${XDG_CACHE_HOME:-$HOME/.cache}/p10k-instant-prompt-${(%):-%n}.zsh" ]]; then
  source "${XDG_CACHE_HOME:-$HOME/.cache}/p10k-instant-prompt-${(%):-%n}.zsh"
fi

# Oh My Zsh configuration
export ZSH="$HOME/.oh-my-zsh"

# Plugins
plugins=(
    git
    sudo
    zsh-autosuggestions
    zsh-syntax-highlighting
    colored-man-pages
    command-not-found
    python
    pip
    virtualenv
)

source $ZSH/oh-my-zsh.sh

# History configuration
HISTSIZE=10000
SAVEHIST=10000
setopt HIST_EXPIRE_DUPS_FIRST
setopt HIST_IGNORE_DUPS
setopt HIST_IGNORE_ALL_DUPS
setopt HIST_IGNORE_SPACE
setopt HIST_FIND_NO_DUPS
setopt HIST_SAVE_NO_DUPS
setopt HIST_BEEP

# Auto-completion settings
autoload -U compinit
compinit

# Case insensitive completion
zstyle ':completion:*' matcher-list 'm:{a-z}={A-Za-z}'

# Better completion menu
zstyle ':completion:*' menu select
zstyle ':completion:*' list-colors "${(s.:.)LS_COLORS}"

# Plugins are loaded automatically by Oh My Zsh from the plugins array above

# Starship prompt
eval "$(starship init zsh)"

# Aliases for better tools
alias cat='bat'
alias grep='rg'
alias find='fd'

# Git aliases
alias ga='git add'
alias gc='git commit'
alias gp='git push'
alias gl='git log --oneline'
alias gd='git diff'

# Development aliases
alias py='python'
alias pip='python -m pip'
alias venv='python -m venv'
alias activate='source venv/bin/activate'


# Enhanced ls aliases
alias ls='eza --icons --group-directories-first'
alias l='eza --icons --group-directories-first'
alias ll='eza -l --icons --group-directories-first --time-style=relative'
alias la='eza -la --icons --group-directories-first --time-style=relative'
alias tree='eza --tree --icons'
alias lt='eza --tree --icons --level=2'
alias lta='eza --tree --icons --level=3 -a'

# Additional aliases
alias clear='clear'
alias reload='source ~/.zshrc'

# Custom functions
mkcd() { 
    mkdir -p "$1" && cd "$1"
    echo "Created and entered: $1"
}

extract() {
    if [ -f "$1" ] ; then
        echo "Extracting $1..."
        case $1 in
            *.tar.bz2)   tar xjf $1     ;;
            *.tar.gz)    tar xzf $1     ;;
            *.bz2)       bunzip2 $1     ;;
            *.rar)       unrar x $1     ;;
            *.gz)        gunzip $1      ;;
            *.tar)       tar xf $1      ;;
            *.tbz2)      tar xjf $1     ;;
            *.tgz)       tar xzf $1     ;;
            *.zip)       unzip $1       ;;
            *.Z)         uncompress $1  ;;
            *.7z)        7z x $1        ;;
            *)          echo "'$1' cannot be extracted via extract()" ;;
        esac
        echo "Extraction complete!"
    else
        echo "'$1' is not a valid file"
    fi
}

# Utility functions
weather() {
    curl -s "wttr.in/$1?format=3"
}

quote() {
    curl -s "https://api.quotegarden.io/api/v3/quotes/random" | jq -r '.data.quoteText + " - " + .data.quoteAuthor' | fold -w 60 -s
}

# Git status function
git_status() {
    echo "Git Status:"
    git status --short --branch
}

# Enhanced cd function
cd() {
    builtin cd "$@"
    if [ $? -eq 0 ]; then
        echo "Now in: $(pwd | sed "s|$HOME|~|")"
        ls --color=auto 2>/dev/null || eza --icons --group-directories-first 2>/dev/null || /bin/ls
    fi
}

# FZF integration (if available)
if [[ -f /usr/share/fzf/key-bindings.zsh ]]; then
    source /usr/share/fzf/key-bindings.zsh
fi

if [[ -f /usr/share/fzf/completion.zsh ]]; then
    source /usr/share/fzf/completion.zsh
fi

# Environment variables for better tool behavior
export BAT_THEME="ansi"
export EDITOR="nvim"
export BROWSER="firefox"

# Color theme environment variables
export FZF_DEFAULT_OPTS="--color=bg+:#3d2f2a,bg:#2d2a2e,spinner:#ffcc5c,hl:#ff6b6b,fg:#f5f0e8,header:#74b9ff,info:#81ecec,pointer:#ffcc5c,marker:#a8e6cf,fg+:#f5f0e8,prompt:#ffcc5c,hl+:#ffb7ba"
export EZA_COLORS="da=1;34:gm=1;35:uu=1;36:un=1;31:gu=1;33:ur=1;32:uw=1;35:ux=1;36:ue=1;37:gr=1;34:gw=1;35:gx=1;36:tr=1;34:tw=1;35:tx=1;36"

# Enhanced zsh options
setopt PROMPT_SUBST
setopt AUTO_CD
setopt GLOB_DOTS

export PYENV_ROOT="$HOME/.pyenv"
[[ -d $PYENV_ROOT/bin ]] && export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init - zsh)"

eval "$(pyenv virtualenv-init -)"