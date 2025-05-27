#!/bin/bash
set -e

SERVER_URL_DEFAULT="http://localhost:8080"
MCP_ENDPOINT_PATH="/mcp" # Default MCP endpoint
TIMEOUT_SECONDS=5

usage() {
    echo "Usage: $0 <subcommand> [options]"
    echo ""
    echo "Subcommands:"
    echo "  list [server_url]              Performs a tools/list request."
    echo "  call <expression> [server_url]      Calls the calculator_tool with an arithmetic expression."
    echo ""
    echo "Arguments:"
    echo "  expression    The arithmetic expression to evaluate (for 'call' subcommand)."
    echo "  server_url    Optional. The base URL of the MCP server (default: ${SERVER_URL_DEFAULT})."
    echo ""
    echo "Examples:"
    echo "  $0 list"
    echo "  $0 call \"2 * (3 + 4)\""
    echo "  $0 call \"10 / 0\" http://custom-server:8080"
    exit 1
}

# Send a request and handle response/errors
send_request() {
    local request_payload="$1"
    local target_url="$2"
    local request_description="$3"

    echo ""
    echo "Sending ${request_description} request to ${target_url}:"
    echo "${request_payload}"
    echo ""

    RESPONSE_FILE=$(mktemp)
    # Ensure cleanup of temp file on exit, SIGHUP, SIGINT, SIGQUIT, SIGTERM
    trap 'rm -f "${RESPONSE_FILE}"; exit' SIGHUP SIGINT SIGQUIT SIGTERM
    trap 'rm -f "${RESPONSE_FILE}"' EXIT


    HTTP_CODE=$(curl -s -L -w "%{http_code}" -X POST \
        --connect-timeout "${TIMEOUT_SECONDS}" \
        -H "Content-Type: application/json" \
        -H "Accept: application/json, text/event-stream" \
        -d "${request_payload}" \
        "${target_url}" -o "${RESPONSE_FILE}")

    CURL_EXIT_CODE=$?

    if [ ${CURL_EXIT_CODE} -ne 0 ]; then
        echo "Error: curl command failed with exit code ${CURL_EXIT_CODE} when sending ${request_description}."
        if [ ${CURL_EXIT_CODE} -eq 7 ]; then 
            echo "Server at ${target_url} refused connection or is not running."
            echo "Please ensure the MCP server is running. Try: ./start-mcp-server.sh or ./start-mcp-server-with-inspector.sh"
        elif [ ${CURL_EXIT_CODE} -eq 28 ]; then 
            echo "Connection to server ${target_url} timed out after ${TIMEOUT_SECONDS} seconds."
        else
            echo "See curl error code for details."
        fi
        exit 1
    fi

    echo "--- Raw Server Response (HTTP Status: ${HTTP_CODE}) ---"
    cat "${RESPONSE_FILE}"
    echo ""
    echo "--- End Raw Server Response ---"

    if [[ "${HTTP_CODE}" -ge 200 && "${HTTP_CODE}" -lt 300 ]]; then
        echo "Formatted JSON Response (from SSE data if applicable):"
        JSON_DATA=$(grep '^data: ' "${RESPONSE_FILE}" | sed 's/^data: //')

        if [[ -n "${JSON_DATA}" ]]; then
            echo "${JSON_DATA}" | python3 -m json.tool
        elif [[ -s "${RESPONSE_FILE}" && ( "$(head -c 1 "${RESPONSE_FILE}")" == "{" || "$(head -c 1 "${RESPONSE_FILE}")" == "[" ) ]]; then
            echo "(Response was not SSE, attempting to parse as plain JSON)"
            python3 -m json.tool < "${RESPONSE_FILE}"
        elif [[ -s "${RESPONSE_FILE}" ]]; then
            echo "Response received, but does not appear to be standard JSON or expected SSE."
        else
            echo "Empty response received from server (HTTP ${HTTP_CODE})."
        fi
    else
        echo "Error: Server responded with HTTP status code ${HTTP_CODE} for ${request_description}."
    fi
    echo ""
}


SUBCOMMAND=$1
if [ -z "${SUBCOMMAND}" ]; then
    usage
fi
shift # Remove subcommand from argument list

case "${SUBCOMMAND}" in
    list)
        SERVER_URL="${1:-$SERVER_URL_DEFAULT}"
        TARGET_URL="${SERVER_URL}${MCP_ENDPOINT_PATH}"
        REQUEST_ID="cli-list-$(date +%s%N)"

        JSON_PAYLOAD=$(cat <<EOF
{
    "jsonrpc": "2.0",
    "method": "tools/list",
    "params": {},
    "id": "${REQUEST_ID}"
}
EOF
)
        send_request "${JSON_PAYLOAD}" "${TARGET_URL}" "tools/list"
        ;;

    call)
        if [ -z "$1" ]; then
            echo "Error: Expression argument is required for 'call' subcommand."
            usage
        fi
        EXPRESSION="$1"
        SERVER_URL="${2:-$SERVER_URL_DEFAULT}"
        TARGET_URL="${SERVER_URL}${MCP_ENDPOINT_PATH}"
        REQUEST_ID="cli-call-$(date +%s%N)"

        JSON_PAYLOAD=$(cat <<EOF
{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
        "name": "calculator_tool",
        "arguments": {
            "expression": "${EXPRESSION}"
        }
    },
    "id": "${REQUEST_ID}"
}
EOF
)
        send_request "${JSON_PAYLOAD}" "${TARGET_URL}" "tools/call (calculator_tool)"
        ;;
    
    *)
        echo "Error: Unknown subcommand '${SUBCOMMAND}'"
        usage
        ;;
esac
