#!/bin/bash

# 🚀 Kubernetes Learning Quick Start
# This script helps you begin your Kubernetes learning journey

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Kubernetes Learning Quick Start${NC}"
echo "======================================"
echo ""

# Function to print section headers
print_section() {
    echo -e "\n${BLUE}$1${NC}"
    echo "----------------------------------------"
}

# Function to wait for user input
wait_for_user() {
    echo -e "\n${GREEN}Press Enter to continue...${NC}"
    read -r
}

# Check prerequisites
check_prerequisites() {
    print_section "Checking Prerequisites"
    
    echo "Checking kubectl installation..."
    if command -v kubectl &> /dev/null; then
        echo -e "${GREEN}✅ kubectl is installed${NC}"
        kubectl version --client --short
    else
        echo -e "${RED}❌ kubectl is not installed${NC}"
        echo "Please install kubectl first: https://kubernetes.io/docs/tasks/tools/"
        exit 1
    fi
    
    echo ""
    echo "Checking cluster connectivity..."
    if kubectl cluster-info &> /dev/null; then
        echo -e "${GREEN}✅ Connected to Kubernetes cluster${NC}"
        kubectl cluster-info
    else
        echo -e "${RED}❌ Cannot connect to Kubernetes cluster${NC}"
        echo "Please ensure your cluster is running and accessible"
        exit 1
    fi
    
    echo ""
    echo "Checking trading-system namespace..."
    if kubectl get namespace trading-system &> /dev/null; then
        echo -e "${GREEN}✅ trading-system namespace exists${NC}"
    else
        echo -e "${YELLOW}⚠️  trading-system namespace does not exist${NC}"
        echo "Creating trading-system namespace..."
        kubectl create namespace trading-system
        echo -e "${GREEN}✅ Created trading-system namespace${NC}"
    fi
}

# Show current cluster status
show_cluster_status() {
    print_section "Current Cluster Status"
    
    echo "Cluster Information:"
    kubectl cluster-info
    echo ""
    
    echo "Nodes:"
    kubectl get nodes
    echo ""
    
    echo "Namespaces:"
    kubectl get namespaces
    echo ""
    
    echo "Resources in trading-system namespace:"
    kubectl get all -n trading-system 2>/dev/null || echo "No resources found in trading-system namespace"
}

# Show learning resources
show_learning_resources() {
    print_section "Available Learning Resources"
    
    echo -e "${GREEN}📚 Your Learning Materials:${NC}"
    echo "1. ${YELLOW}KUBERNETES_LEARNING_PLAN.md${NC} - Your personalized 8-week learning plan"
    echo "2. ${YELLOW}KUBERNETES_COMMAND_REFERENCE.md${NC} - Quick command reference"
    echo "3. ${YELLOW}docs/KUBERNETES_LEARNING_GUIDE.md${NC} - Comprehensive guide with diagrams"
    echo "4. ${YELLOW}scripts/k8s-learning-exercises.sh${NC} - Interactive hands-on exercises"
    echo ""
    
    echo -e "${GREEN}🎯 Quick Access Commands:${NC}"
    echo "• make -f Makefile.kubernetes k8s-learning-plan    - Open learning plan"
    echo "• make -f Makefile.kubernetes k8s-command-ref       - Open command reference"
    echo "• make -f Makefile.kubernetes k8s-learn            - Open comprehensive guide"
    echo "• make -f Makefile.kubernetes k8s-learn-exercises  - Run interactive exercises"
    echo ""
    
    echo -e "${GREEN}🔧 Practice Commands:${NC}"
    echo "• make -f Makefile.kubernetes k8s-practice-basic    - Practice basic operations"
    echo "• make -f Makefile.kubernetes k8s-practice-debug    - Practice debugging"
    echo "• make -f Makefile.kubernetes k8s-practice-resources - Practice resource management"
    echo "• make -f Makefile.kubernetes k8s-status-all        - Get comprehensive status"
}

# Show immediate next steps
show_next_steps() {
    print_section "Your Next Steps"
    
    echo -e "${GREEN}🎯 Immediate Actions (Choose One):${NC}"
    echo ""
    echo "1. ${YELLOW}Start with Learning Plan${NC}"
    echo "   Run: make -f Makefile.kubernetes k8s-learning-plan"
    echo "   This will open your personalized 8-week learning plan"
    echo ""
    echo "2. ${YELLOW}Run Interactive Exercises${NC}"
    echo "   Run: make -f Makefile.kubernetes k8s-learn-exercises"
    echo "   This will start hands-on exercises with guided practice"
    echo ""
    echo "3. ${YELLOW}Practice Basic Commands${NC}"
    echo "   Run: make -f Makefile.kubernetes k8s-practice-basic"
    echo "   This will show you basic cluster operations"
    echo ""
    echo "4. ${YELLOW}Deploy Your First Service${NC}"
    echo "   Run: make -f Makefile.kubernetes k8s-deploy-strategy-service"
    echo "   This will deploy a service from your trading system"
    echo ""
    echo "5. ${YELLOW}Check Command Reference${NC}"
    echo "   Run: make -f Makefile.kubernetes k8s-command-ref"
    echo "   This will open the command reference guide"
}

# Show your project's Kubernetes setup
show_project_setup() {
    print_section "Your Project's Kubernetes Setup"
    
    echo -e "${GREEN}📁 Your Kubernetes Files:${NC}"
    echo "• ${YELLOW}k8s/${NC} - Contains 68+ Kubernetes YAML files"
    echo "• ${YELLOW}Makefile.kubernetes${NC} - Contains 50+ Kubernetes commands"
    echo "• ${YELLOW}k8s/README.md${NC} - Your cluster documentation"
    echo ""
    
    echo -e "${GREEN}🚀 Your Services:${NC}"
    echo "• Strategy Service - Core trading logic"
    echo "• Market Data Service - Real-time market data"
    echo "• Backtest API - Backtesting endpoints"
    echo "• Dashboard Services - Web interfaces"
    echo "• Database Services - PostgreSQL and Redis"
    echo "• Message Broker - RabbitMQ"
    echo ""
    
    echo -e "${GREEN}🎯 Your Learning Advantage:${NC}"
    echo "✅ Real-world application to practice on"
    echo "✅ Comprehensive YAML examples"
    echo "✅ Production-ready configurations"
    echo "✅ Multiple service types to learn from"
    echo "✅ Job and CronJob examples"
    echo "✅ Resource management examples"
}

# Show daily practice routine
show_daily_routine() {
    print_section "Recommended Daily Practice Routine"
    
    echo -e "${GREEN}🌅 Morning (15 minutes):${NC}"
    echo "1. Check cluster status: make -f Makefile.kubernetes k8s-status-all"
    echo "2. Review one concept from your learning plan"
    echo "3. Practice one command from the reference guide"
    echo ""
    
    echo -e "${GREEN}🌞 Afternoon (30 minutes):${NC}"
    echo "1. Run one exercise from: make -f Makefile.kubernetes k8s-learn-exercises"
    echo "2. Deploy and manage one of your services"
    echo "3. Practice debugging with: make -f Makefile.kubernetes k8s-practice-debug"
    echo ""
    
    echo -e "${GREEN}🌙 Evening (15 minutes):${NC}"
    echo "1. Review what you learned"
    echo "2. Update your progress checklist"
    echo "3. Plan tomorrow's learning focus"
    echo ""
    
    echo -e "${GREEN}📈 Weekly Goals:${NC}"
    echo "• Complete one week of your learning plan"
    echo "• Master 5 new kubectl commands"
    echo "• Successfully deploy and manage one service"
    echo "• Debug and fix one issue"
    echo "• Understand one new Kubernetes concept"
}

# Main menu
show_menu() {
    echo -e "\n${GREEN}Quick Start Options:${NC}"
    echo "1. Check Prerequisites"
    echo "2. Show Cluster Status"
    echo "3. Show Learning Resources"
    echo "4. Show Next Steps"
    echo "5. Show Project Setup"
    echo "6. Show Daily Practice Routine"
    echo "7. Run All Checks"
    echo "8. Exit"
    echo -e "\nEnter your choice (1-8): "
}

# Main execution
main() {
    while true; do
        show_menu
        read -r choice
        
        case $choice in
            1) check_prerequisites ;;
            2) show_cluster_status ;;
            3) show_learning_resources ;;
            4) show_next_steps ;;
            5) show_project_setup ;;
            6) show_daily_routine ;;
            7)
                echo -e "\n${GREEN}Running all checks and showing complete overview...${NC}"
                check_prerequisites
                wait_for_user
                show_cluster_status
                wait_for_user
                show_learning_resources
                wait_for_user
                show_project_setup
                wait_for_user
                show_next_steps
                wait_for_user
                show_daily_routine
                ;;
            8)
                echo -e "\n${GREEN}Happy learning! Remember: Practice makes perfect! 🚀${NC}"
                echo ""
                echo "Quick reminder of your next steps:"
                echo "• make -f Makefile.kubernetes k8s-learning-plan"
                echo "• make -f Makefile.kubernetes k8s-learn-exercises"
                echo "• make -f Makefile.kubernetes k8s-practice-basic"
                exit 0
                ;;
            *)
                echo -e "\n${RED}Invalid choice. Please enter 1-8.${NC}"
                ;;
        esac
        
        wait_for_user
    done
}

# Run main function
main
