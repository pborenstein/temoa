#!/usr/bin/env bash
# Temoa API Smoke Test
# Quick validation of server endpoints
#
# Usage:
#   ./scripts/test_api.sh [BASE_URL]
#
# Examples:
#   ./scripts/test_api.sh                    # Test localhost
#   ./scripts/test_api.sh http://100.x.x.x:8080  # Test via Tailscale

set -euo pipefail

# Configuration
BASE_URL="${1:-http://localhost:8080}"
TIMEOUT=10

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if jq is available
if ! command -v jq &> /dev/null; then
    echo -e "${YELLOW}⚠️  jq not found. Install for prettier output: brew install jq${NC}"
    USE_JQ=false
else
    USE_JQ=true
fi

# Helper functions
print_header() {
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

test_endpoint() {
    local name="$1"
    local endpoint="$2"
    local expected_key="$3"  # Key that should exist in response

    echo -e "${YELLOW}Testing: ${NC}${endpoint}"

    if response=$(curl -s --max-time "$TIMEOUT" "${BASE_URL}${endpoint}" 2>&1); then
        if $USE_JQ; then
            # Pretty print with jq
            echo "$response" | jq .

            # Check if expected key exists
            if [ -n "$expected_key" ] && echo "$response" | jq -e ".$expected_key" > /dev/null 2>&1; then
                echo -e "${GREEN}✓ ${name} passed${NC}"
                return 0
            elif [ -z "$expected_key" ]; then
                echo -e "${GREEN}✓ ${name} passed${NC}"
                return 0
            else
                echo -e "${RED}✗ ${name} failed: Missing expected key '${expected_key}'${NC}"
                return 1
            fi
        else
            # Plain output without jq
            echo "$response"
            if [ -n "$expected_key" ] && echo "$response" | grep -q "\"$expected_key\""; then
                echo -e "${GREEN}✓ ${name} passed${NC}"
                return 0
            elif [ -z "$expected_key" ]; then
                echo -e "${GREEN}✓ ${name} passed${NC}"
                return 0
            else
                echo -e "${RED}✗ ${name} failed${NC}"
                return 1
            fi
        fi
    else
        echo -e "${RED}✗ ${name} failed: Connection error${NC}"
        echo "$response"
        return 1
    fi
}

# Main test execution
main() {
    print_header "🔍 Temoa API Smoke Test"
    echo "Testing: ${BASE_URL}"
    echo "Timeout: ${TIMEOUT}s"

    PASSED=0
    FAILED=0

    # Test 1: Health Check
    print_header "🏥 Health Check"
    if test_endpoint "Health" "/health" "status"; then
        ((PASSED++))
    else
        ((FAILED++))
    fi

    # Test 2: Stats
    print_header "📊 Vault Statistics"
    if test_endpoint "Stats" "/stats" "model_info"; then
        ((PASSED++))
    else
        ((FAILED++))
    fi

    # Test 3: Search
    print_header "🔍 Search Endpoint"
    if test_endpoint "Search" "/search?q=test&limit=3" "results"; then
        ((PASSED++))
    else
        ((FAILED++))
    fi

    # Test 4: Root (UI)
    print_header "🎨 Web UI"
    echo -e "${YELLOW}Testing: ${NC}/"
    if response=$(curl -s --max-time "$TIMEOUT" "${BASE_URL}/" 2>&1); then
        if echo "$response" | grep -q "<title.*Temoa.*</title>"; then
            echo -e "${GREEN}✓ UI loaded (contains 'Temoa' title)${NC}"
            ((PASSED++))
        else
            echo -e "${RED}✗ UI failed: Missing Temoa title${NC}"
            ((FAILED++))
        fi
    else
        echo -e "${RED}✗ UI failed: Connection error${NC}"
        ((FAILED++))
    fi

    # Test 5: OpenAPI Docs
    print_header "📖 API Documentation"
    echo -e "${YELLOW}Testing: ${NC}/docs"
    if response=$(curl -s --max-time "$TIMEOUT" "${BASE_URL}/docs" 2>&1); then
        if echo "$response" | grep -q "swagger"; then
            echo -e "${GREEN}✓ OpenAPI docs accessible${NC}"
            echo "   View at: ${BASE_URL}/docs"
            ((PASSED++))
        else
            echo -e "${RED}✗ OpenAPI docs failed${NC}"
            ((FAILED++))
        fi
    else
        echo -e "${RED}✗ OpenAPI docs failed: Connection error${NC}"
        ((FAILED++))
    fi

    # Summary
    print_header "📊 Test Summary"
    echo -e "Passed: ${GREEN}${PASSED}${NC}"
    echo -e "Failed: ${RED}${FAILED}${NC}"
    echo ""

    if [ "$FAILED" -eq 0 ]; then
        echo -e "${GREEN}🎉 All tests passed!${NC}"
        echo ""
        echo "Next steps:"
        echo "  • Access UI: ${BASE_URL}/"
        echo "  • View API docs: ${BASE_URL}/docs"
        echo "  • Try a search from mobile via Tailscale"
        return 0
    else
        echo -e "${RED}❌ Some tests failed${NC}"
        echo ""
        echo "Troubleshooting:"
        echo "  • Check if server is running: curl ${BASE_URL}/health"
        echo "  • View server logs for errors"
        echo "  • Verify config.json is correct"
        return 1
    fi
}

# Run tests
main
