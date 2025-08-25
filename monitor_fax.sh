#!/bin/bash

# Real-time Fax Monitoring Script
# Monitors fax transactions in real-time

API="http://127.0.0.1:8585"
TOKEN="4165e5b65875b10f38eb015ae5b9e9a0512e3cd1"
REFRESH_INTERVAL=${1:-5}  # Default 5 seconds

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Function to get transaction stats
get_stats() {
    curl -s -X GET \
        -H "Authorization: Token $TOKEN" \
        "$API/api/fax/list/" 2>/dev/null
}

# Function to format status with color
format_status() {
    case $1 in
        "sent")
            echo -e "${GREEN}SENT${NC}"
            ;;
        "failed")
            echo -e "${RED}FAILED${NC}"
            ;;
        "processing")
            echo -e "${YELLOW}PROCESSING${NC}"
            ;;
        "pending")
            echo -e "${CYAN}PENDING${NC}"
            ;;
        *)
            echo "$1"
            ;;
    esac
}

# Function to format direction
format_direction() {
    case $1 in
        "outbound")
            echo -e "${BLUE}→ OUT${NC}"
            ;;
        "inbound")
            echo -e "${GREEN}← IN ${NC}"
            ;;
        *)
            echo "$1"
            ;;
    esac
}

# Main monitoring loop
echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║              FAX TRANSACTION MONITOR                        ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo "Refreshing every $REFRESH_INTERVAL seconds. Press Ctrl+C to stop."
echo ""

while true; do
    clear
    echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║              FAX TRANSACTION MONITOR                        ║${NC}"
    echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo "Last Update: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "Refresh Rate: ${REFRESH_INTERVAL}s"
    echo ""
    
    # Get data
    response=$(get_stats)
    
    if [ -z "$response" ]; then
        echo -e "${RED}Error: Cannot connect to API${NC}"
    else
        # Parse statistics
        total=$(echo "$response" | python -c "import sys, json; print(json.load(sys.stdin)['count'])" 2>/dev/null)
        
        echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
        echo -e "Total Transactions: ${GREEN}$total${NC}"
        echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
        echo ""
        
        # Display recent transactions
        echo "Recent Transactions (Latest 10):"
        echo "────────────────────────────────────────────────────────────────"
        printf "%-8s %-37s %-10s %-15s %-15s\n" "DIR" "UUID" "STATUS" "FROM" "TO"
        echo "────────────────────────────────────────────────────────────────"
        
        echo "$response" | python -c "
import sys, json
data = json.load(sys.stdin)
for item in data['results'][:10]:
    print(f\"{item['direction']}|{item['uuid']}|{item['status']}|{item['sender_number'][:12]}|{item['recipient_number'][:12]}\")
" 2>/dev/null | while IFS='|' read -r direction uuid status sender recipient; do
            dir_formatted=$(format_direction "$direction")
            status_formatted=$(format_status "$status")
            printf "%-8s %-37s %-10s %-15s %-15s\n" \
                "$dir_formatted" "$uuid" "$status_formatted" "$sender" "$recipient"
        done
        
        echo ""
        echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
        
        # Status breakdown
        echo ""
        echo "Status Breakdown:"
        echo "────────────────────"
        
        sent_count=$(echo "$response" | python -c "
import sys, json
data = json.load(sys.stdin)
print(len([x for x in data['results'] if x['status'] == 'sent']))
" 2>/dev/null)
        
        failed_count=$(echo "$response" | python -c "
import sys, json
data = json.load(sys.stdin)
print(len([x for x in data['results'] if x['status'] == 'failed']))
" 2>/dev/null)
        
        processing_count=$(echo "$response" | python -c "
import sys, json
data = json.load(sys.stdin)
print(len([x for x in data['results'] if x['status'] == 'processing']))
" 2>/dev/null)
        
        pending_count=$(echo "$response" | python -c "
import sys, json
data = json.load(sys.stdin)
print(len([x for x in data['results'] if x['status'] == 'pending']))
" 2>/dev/null)
        
        echo -e "  $(format_status 'sent'):       $sent_count"
        echo -e "  $(format_status 'failed'):     $failed_count"
        echo -e "  $(format_status 'processing'): $processing_count"
        echo -e "  $(format_status 'pending'):    $pending_count"
    fi
    
    echo ""
    echo -e "${YELLOW}Press Ctrl+C to exit${NC}"
    
    sleep $REFRESH_INTERVAL
done