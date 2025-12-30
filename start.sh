#!/bin/bash

# HealthInsight Docker Startup Script
# Makes it easy to start development or production environment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🏥 HealthInsight Docker Setup${NC}"
echo "=================================="

# Function to check if Docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        echo -e "${RED}❌ Docker is not running. Please start Docker first.${NC}"
        exit 1
    fi
}

# Function to check if Docker Compose is available
check_docker_compose() {
    if ! command -v docker-compose &> /dev/null; then
        echo -e "${RED}❌ Docker Compose is not installed.${NC}"
        exit 1
    fi
}

# Function to show help
show_help() {
    echo -e "${YELLOW}Usage: $0 [OPTION]${NC}"
    echo "Options:"
    echo "  dev         Start development environment"
    echo "  prod        Start production environment"
    echo "  build       Build all images"
    echo "  stop        Stop all services"
    echo "  clean       Clean up containers and volumes"
    echo "  logs        Show logs for all services"
    echo "  help        Show this help message"
    echo ""
    echo "Development mode includes:"
    echo "  - Hot reload for backend and frontend"
    echo "  - MongoDB UI at http://localhost:8081"
    echo ""
    echo "Production mode includes:"
    echo "  - Optimized builds"
    echo "  - No source code mounting"
    echo "  - All health checks enabled"
}

# Function to start development environment
start_dev() {
    echo -e "${GREEN}🚀 Starting development environment...${NC}"
    echo -e "${BLUE}This will start:${NC}"
    echo "  • MongoDB (port 27017)"
    echo "  • Backend API (port 8000) - Hot reload enabled"
    echo "  • Frontend (port 5173) - Hot reload enabled"
    echo "  • MongoDB UI (port 8081)"
    echo ""
    echo -e "${YELLOW}Note: Frontend will be proxied to backend API${NC}"
    
    docker-compose --profile dev up --build
}

# Function to start production environment
start_prod() {
    echo -e "${GREEN}🚀 Starting production environment...${NC}"
    echo -e "${BLUE}This will start:${NC}"
    echo "  • MongoDB (port 27017)"
    echo "  • Backend API (port 8000)"
    echo "  • Frontend (port 5173)"
    echo ""
    echo -e "${YELLOW}Note: This uses optimized production builds${NC}"
    
    docker-compose up --build -d
    echo -e "${GREEN}✅ Production environment started!${NC}"
    echo -e "${BLUE}Access your app at: http://localhost:5173${NC}"
}

# Function to build images
build_images() {
    echo -e "${GREEN}🔨 Building all Docker images...${NC}"
    docker-compose build --no-cache
    echo -e "${GREEN}✅ Build completed!${NC}"
}

# Function to stop services
stop_services() {
    echo -e "${YELLOW}🛑 Stopping all services...${NC}"
    docker-compose down
    echo -e "${GREEN}✅ Services stopped!${NC}"
}

# Function to clean up
clean_up() {
    echo -e "${RED}🧹 Cleaning up containers and volumes...${NC}"
    read -p "⚠️  This will delete all data. Are you sure? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker-compose down -v --remove-orphans
        docker system prune -f
        echo -e "${GREEN}✅ Cleanup completed!${NC}"
    else
        echo -e "${YELLOW}Cleanup cancelled.${NC}"
    fi
}

# Function to show logs
show_logs() {
    echo -e "${BLUE}📋 Showing logs for all services...${NC}"
    echo -e "${YELLOW}Press Ctrl+C to stop watching logs${NC}"
    docker-compose logs -f
}

# Function to check service health
check_health() {
    echo -e "${BLUE}🏥 Checking service health...${NC}"
    
    echo "Frontend: $(curl -s http://localhost:5173/health > /dev/null && echo "${GREEN}✅ Healthy${NC}" || echo "${RED}❌ Unhealthy${NC}")"
    echo "Backend:  $(curl -s http://localhost:8000/api/ping > /dev/null && echo "${GREEN}✅ Healthy${NC}" || echo "${RED}❌ Unhealthy${NC}")"
    
    if docker-compose ps | grep -q mongo-express; then
        echo "Mongo UI:  $(curl -s http://localhost:8081 > /dev/null && echo "${GREEN}✅ Healthy${NC}" || echo "${RED}❌ Unhealthy${NC}")"
    fi
}

# Main script logic
case "${1:-help}" in
    dev)
        check_docker
        check_docker_compose
        start_dev
        ;;
    prod)
        check_docker
        check_docker_compose
        start_prod
        ;;
    build)
        check_docker
        check_docker_compose
        build_images
        ;;
    stop)
        stop_services
        ;;
    clean)
        clean_up
        ;;
    logs)
        show_logs
        ;;
    health)
        check_health
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo -e "${RED}❌ Unknown option: $1${NC}"
        show_help
        exit 1
        ;;
esac
