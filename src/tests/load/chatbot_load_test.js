import http from 'k6/http';
import { check, sleep, group } from 'k6';
import { Rate, Trend } from 'k6/metrics';
import { textSummary } from 'https://jslib.k6.io/k6-summary/0.0.1/index.js';

// Custom metrics
export let errorRate = new Rate('errors');
export let requestDuration = new Trend('request_duration');
export let successRate = new Rate('success_rate');

// Configuration
const BASE_URL_OAUTH = __ENV.BASE_URL_OAUTH || 'http://localhost:8001/oauth/v1';
const BASE_URL_CHAT = __ENV.BASE_URL_CHAT || 'http://localhost:8002/langgpt/v1';
const CLIENT_ID = __ENV.CLIENT_ID || 'ai_develop_01';
const CLIENT_SECRET = __ENV.CLIENT_SECRET || 'abc123';

// Test configuration
export let options = {
    stages: [
        { duration: '10s', target: 2 },  // Start with 2 users
        { duration: '30s', target: 2 },  // Stay at 2 users
        { duration: '20s', target: 5 },  // Ramp up to 5 users
        { duration: '30s', target: 5 },  // Stay at 5 users
        { duration: '10s', target: 0 },  // Ramp down to 0
    ],
    thresholds: {
        http_req_duration: ['p(95)<5000'],  // 95% of requests should be below 5s
        'http_req_duration{type:chat}': ['p(95)<10000'],  // Chat requests below 10s
        errors: ['rate<0.1'],  // Error rate should be below 10%
    },
};

// Get auth token
function getAuthToken() {
    const tokenResponse = http.post(`${BASE_URL_OAUTH}/token/`, null, {
        headers: {
            'client-id': CLIENT_ID,
            'client-secret': CLIENT_SECRET,
        },
    });

    const success = check(tokenResponse, {
        'Token generated successfully': (r) => r.status === 200,
    });

    if (!success) {
        console.error(`Failed to get token: ${tokenResponse.status} ${tokenResponse.body}`);
        return null;
    }

    return tokenResponse.json('access_token');
}

export default function () {
    const token = getAuthToken();
    if (!token) {
        errorRate.add(1);
        return;
    }

    group('Chat API Tests', function () {
        // Test chat endpoint
        const chatPayload = {
            user_id: __VU % 2 === 0 ? "dev_test006" : "dev_test007",  // Alternate between valid user IDs
            topic_id: `topic_${__VU}_${__ITER}`,
            question: 'What is your name?',
            model: 'GPT'
        };

        const chatResponse = http.post(
            `${BASE_URL_CHAT}/ask/`,
            JSON.stringify(chatPayload),
            {
                headers: {
                    'Content-Type': 'application/json',
                    'token': `Bearer ${token}`,
                },
                tags: { type: 'chat' },
            }
        );

        // Record metrics
        const chatSuccess = check(chatResponse, {
            'Chat status is 200': (r) => r.status === 200,
            'Chat response has data': (r) => {
                try {
                    const json = r.json();
                    return json.data !== undefined;
                } catch (e) {
                    console.error(`Failed to parse chat response: ${r.body}`);
                    return false;
                }
            },
        });

        successRate.add(chatSuccess);
        errorRate.add(!chatSuccess);
        requestDuration.add(chatResponse.timings.duration);

        if (!chatSuccess) {
            console.error(`Chat request failed: ${chatResponse.status} ${chatResponse.body}`);
            return;
        }

        // Test conversation history
        const historyPayload = {
            user_id: __VU % 2 === 0 ? "dev_test006" : "dev_test007",  // Use same user_id as chat request
            topic_id: `topic_${__VU}_${__ITER}`
        };

        const historyResponse = http.post(
            `${BASE_URL_CHAT}/conversation/`,
            JSON.stringify(historyPayload),
            {
                headers: {
                    'Content-Type': 'application/json',
                    'token': `Bearer ${token}`,
                },
                tags: { type: 'history' },
            }
        );

        const historySuccess = check(historyResponse, {
            'History status is 200': (r) => r.status === 200,
            'History response has data': (r) => {
                try {
                    const json = r.json();
                    return json.data !== undefined;
                } catch (e) {
                    console.error(`Failed to parse history response: ${r.body}`);
                    return false;
                }
            },
        });

        if (!historySuccess) {
            console.error(`History request failed: ${historyResponse.status} ${historyResponse.body}`);
        }

        // Add delay between iterations to prevent overwhelming the API
        sleep(1);
    });
}

// Handle summary report
export function handleSummary(data) {
    return {
        stdout: textSummary(data, { indent: ' ', enableColors: true }),
        'src/tests/load/summary.json': JSON.stringify(data),
    };
}
