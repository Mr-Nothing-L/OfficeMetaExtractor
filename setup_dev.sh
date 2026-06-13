#!/bin/bash
# ============================================================================
# OfficeMetaExtractor - macOS 开发环境一键配置脚本
# Python 3.9.6 兼容版本
# ============================================================================

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目配置
PROJECT_NAME="OfficeMetaExtractor"
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$PROJECT_DIR/venv"
REQUIREMENTS_FILE="$PROJECT_DIR/requirements.txt"

# 打印带颜色的信息
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查命令是否存在
check_command() {
    if command -v "$1" &> /dev/null; then
        return 0
    else
        return 1
    fi
}

# ============================================================================
# 步骤 1: 检查 Python 版本
# ============================================================================
check_python() {
    print_info "检查 Python 版本..."
    
    if ! check_command python3; then
        print_error "未找到 python3，请先安装 Python 3.9+"
        print_info "建议通过 Homebrew 安装: brew install python@3.9"
        exit 1
    fi
    
    PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
    PYTHON_MAJOR=$(echo "$PYTHON_VERSION" | cut -d. -f1)
    PYTHON_MINOR=$(echo "$PYTHON_VERSION" | cut -d. -f2)
    
    print_info "检测到 Python 版本: $PYTHON_VERSION"
    
    # 检查是否为 3.9.x
    if [[ "$PYTHON_MAJOR" -eq 3 && "$PYTHON_MINOR" -eq 9 ]]; then
        print_success "Python 3.9.x 已满足项目要求"
    elif [[ "$PYTHON_MAJOR" -eq 3 && "$PYTHON_MINOR" -ge 8 && "$PYTHON_MINOR" -le 9 ]]; then
        print_warning "Python $PYTHON_VERSION 可用，但项目推荐 3.9.x"
    else
        print_error "Python $PYTHON_VERSION 不兼容，项目需要 3.8-3.9"
        print_info "建议安装 Python 3.9: brew install python@3.9"
        exit 1
    fi
}

# ============================================================================
# 步骤 2: 检查并安装 Homebrew（可选，用于安装系统工具）
# ============================================================================
check_brew() {
    print_info "检查 Homebrew..."
    
    if check_command brew; then
        BREW_VERSION=$(brew --version | head -n1)
        print_success "$BREW_VERSION"
    else
        print_warning "未安装 Homebrew，部分系统工具（如 UPX）需要手动安装"
        print_info "如需安装 Homebrew，运行:"
        print_info '/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'
    fi
}

# ============================================================================
# 步骤 3: 检查 Xcode Command Line Tools（Cython 编译需要）
# ============================================================================
check_xcode_tools() {
    print_info "检查 Xcode Command Line Tools..."
    
    if xcode-select -p &> /dev/null; then
        print_success "Xcode Command Line Tools 已安装"
    else
        print_warning "未安装 Xcode Command Line Tools"
        print_info "正在安装...（可能需要几分钟）"
        xcode-select --install
        print_info "请按提示完成安装，然后重新运行此脚本"
        exit 1
    fi
}

# ============================================================================
# 步骤 4: 检查 UPX（可选，用于压缩 EXE）
# ============================================================================
check_upx() {
    print_info "检查 UPX..."
    
    if check_command upx; then
        UPX_VERSION=$(upx --version | head -n1)
        print_success "UPX 已安装: $UPX_VERSION"
    else
        print_warning "未安装 UPX（可选，用于压缩 Windows EXE）"
        if check_command brew; then
            print_info "可通过 Homebrew 安装: brew install upx"
        fi
        print_info "Windows EXE 构建将在 GitHub Actions 中完成，macOS 本地开发可不安装"
    fi
}

# ============================================================================
# 步骤 5: 创建虚拟环境
# ============================================================================
setup_venv() {
    print_info "设置 Python 虚拟环境..."
    
    if [[ -d "$VENV_DIR" ]]; then
        print_warning "虚拟环境已存在: $VENV_DIR"
        read -p "是否重新创建？(y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            print_info "删除旧虚拟环境..."
            rm -rf "$VENV_DIR"
        else
            print_info "使用现有虚拟环境"
            return
        fi
    fi
    
    print_info "创建虚拟环境..."
    python3 -m venv "$VENV_DIR"
    print_success "虚拟环境创建完成"
}

# ============================================================================
# 步骤 6: 安装 Python 依赖
# ============================================================================
install_dependencies() {
    print_info "安装 Python 依赖..."
    
    # 激活虚拟环境
    source "$VENV_DIR/bin/activate"
    
    # 升级 pip
    print_info "升级 pip..."
    pip install --upgrade pip
    
    # 检查 requirements.txt
    if [[ ! -f "$REQUIREMENTS_FILE" ]]; then
        print_error "未找到 requirements.txt: $REQUIREMENTS_FILE"
        exit 1
    fi
    
    # 安装依赖
    print_info "安装项目依赖（可能需要几分钟）..."
    pip install -r "$REQUIREMENTS_FILE"
    
    print_success "依赖安装完成"
}

# ============================================================================
# 步骤 7: 验证安装
# ============================================================================
verify_installation() {
    print_info "验证安装..."
    
    source "$VENV_DIR/bin/activate"
    
    # 检查关键包
    local packages=("PyQt5" "docx" "openpyxl" "pptx" "olefile" "PyPDF2" "Cython" "PyInstaller")
    local all_ok=true
    
    for pkg in "${packages[@]}"; do
        if python3 -c "import $pkg" 2>/dev/null; then
            version=$(python3 -c "import $pkg; print(getattr($pkg, '__version__', 'unknown'))" 2>/dev/null || echo "unknown")
            print_success "$pkg 已安装 (版本: $version)"
        else
            print_error "$pkg 安装失败"
            all_ok=false
        fi
    done
    
    if $all_ok; then
        print_success "所有关键包验证通过"
    else
        print_error "部分包验证失败，请检查安装日志"
        exit 1
    fi
}

# ============================================================================
# 步骤 8: 创建便捷启动脚本
# ============================================================================
create_launcher() {
    print_info "创建便捷启动脚本..."
    
    local launcher="$PROJECT_DIR/run.sh"
    cat > "$launcher" << 'EOF'
#!/bin/bash
# OfficeMetaExtractor 启动脚本
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$PROJECT_DIR/venv/bin/activate"
python "$PROJECT_DIR/main.py" "$@"
EOF
    
    chmod +x "$launcher"
    print_success "启动脚本已创建: $launcher"
    print_info "使用方式: ./run.sh"
}

# ============================================================================
# 步骤 9: 显示环境信息
# ============================================================================
show_env_info() {
    echo
    echo "========================================"
    echo "   OfficeMetaExtractor 开发环境配置完成"
    echo "========================================"
    echo
    echo "项目目录: $PROJECT_DIR"
    echo "虚拟环境: $VENV_DIR"
    echo "Python 版本: $(python3 --version)"
    echo
    echo "常用命令:"
    echo "  激活虚拟环境: source venv/bin/activate"
    echo "  运行项目:     python main.py"
    echo "  快速启动:     ./run.sh"
    echo
    echo "GitHub Actions 配置:"
    echo "  仓库: https://github.com/Mr-Nothing-L/OfficeMetaExtractor"
    echo "  推送代码后自动触发 Windows EXE 构建"
    echo
    echo "下一步:"
    echo "  1. 运行项目测试: ./run.sh"
    echo "  2. 配置 GitHub Actions: .github/workflows/build.yml"
    echo "  3. 开发完成后推送代码，自动构建 Windows EXE"
    echo
}

# ============================================================================
# 主流程
# ============================================================================
main() {
    echo "========================================"
    echo "   OfficeMetaExtractor 环境配置"
    echo "   macOS 开发环境一键配置"
    echo "========================================"
    echo
    
    check_python
    check_brew
    check_xcode_tools
    check_upx
    setup_venv
    install_dependencies
    verify_installation
    create_launcher
    show_env_info
    
    print_success "配置完成！"
}

# 运行主流程
main
