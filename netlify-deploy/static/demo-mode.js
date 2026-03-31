/* ═══════════════════════════════════════════════════════════════════════
   Demo Mode — Intercepts API calls with realistic mock data
   so the frontend works standalone on Netlify without a backend.
   ═══════════════════════════════════════════════════════════════════════ */

const DEMO_DASHBOARD = {
    total: 16,
    draft: 2,
    review: 3,
    approved: 6,
    scheduled: 3,
    published: 2,
    recent: [
        { platform: "linkedin", title: "Hedge Fund Access for RIAs", content_type: "linkedin_post", status: "approved", updated_at: new Date(Date.now() - 3600000).toISOString() },
        { platform: "twitter", title: "60/40 Portfolio Correlation Thread", content_type: "twitter_thread", status: "review", updated_at: new Date(Date.now() - 7200000).toISOString() },
        { platform: "newsletter", title: "Q1 Alternatives Outlook", content_type: "newsletter_blurb", status: "scheduled", updated_at: new Date(Date.now() - 10800000).toISOString() },
        { platform: "email", title: "Tender Offer Fund Launch", content_type: "email_snippet", status: "approved", updated_at: new Date(Date.now() - 14400000).toISOString() },
        { platform: "blog", title: "Why Multi-Strategy Belongs in Every RIA Portfolio", content_type: "blog_post", status: "published", updated_at: new Date(Date.now() - 86400000).toISOString() },
    ]
};

const DEMO_GENERATE = {
    analysis: {
        topic: "Hedge fund access & 60/40 portfolio limitations",
        input_type: "voice_memo",
        sentiment: "confident, authoritative",
        key_points: ["60/40 correlation breakdown", "RIA infrastructure gap", "Tender offer fund solution"]
    },
    method: "claude-template",
    content: {
        linkedin: `The 60/40 portfolio is broken — and the data proves it.\n\nIn 2022, the correlation between stocks and bonds hit 95%. That's not diversification. That's concentration with extra steps.\n\nHere's what I'm seeing talking to $2-10B independent RIAs every week:\n\n→ They KNOW they need alternatives exposure\n→ They DON'T have the infrastructure to access institutional hedge funds\n→ Managing 5 separate LP agreements is an operational nightmare\n\nThis is exactly why we built the Equi tender offer fund.\n\nOne allocation. Full diversification across institutional-quality hedge fund strategies. Quarterly liquidity. Custodial compatibility with Schwab, Fidelity, and Pershing.\n\nThe RIAs who build alternatives capability now will have a structural advantage for the next decade.\n\nThe ones who wait will spend years catching up.\n\n#alternatives #hedgefunds #RIA #wealthmanagement #portfolioconstruction`,

        newsletter: `THE 60/40 PROBLEM — AND THE SOLUTION MOST RIAS ARE MISSING\n\nThe numbers don't lie: stock-bond correlation hit 95% in 2022, fundamentally breaking the diversification assumption behind traditional portfolios. Independent RIAs managing $2-10B know they need hedge fund exposure — but face three barriers: access (high minimums), diligence (different skillset), and operations (LP agreements, K-1s, capital calls).\n\nEqui's tender offer fund solves all three. One allocation provides diversified, institutional-quality hedge fund exposure through existing custodial relationships. No operational nightmare. No five separate LP agreements.\n\nAs BlackRock tells institutional clients to increase hedge fund allocations, the question isn't whether RIAs should add alternatives — it's whether they can afford not to.`,

        twitter_thread: [
            "🧵 The 60/40 portfolio assumption is dead. Here's why — and what smart RIAs are doing about it.",
            "In 2022, the correlation between stocks and bonds hit 95%.\n\nThat means your \"diversified\" portfolio was essentially a single bet.\n\nThis wasn't a blip — rolling 12-month correlation stayed above 60% through most of 2023.",
            "The problem isn't awareness. Every RIA I talk to knows they need alternatives.\n\nThe problem is infrastructure:\n\n→ $5-10M hedge fund minimums\n→ Complex LP agreements\n→ K-1s and capital calls\n→ No in-house diligence team",
            "The endowment model (Yale, Harvard, Stanford) has allocated 25-40% to alternatives for decades.\n\nTheir returns have crushed 60/40 benchmarks.\n\nBut they have 50-person investment teams. The average RIA has 5.",
            "That's the gap we built @JoinEqui to fill.\n\nOur tender offer fund gives RIAs institutional-quality hedge fund exposure through ONE allocation.\n\n✅ Quarterly liquidity\n✅ Works with Schwab/Fidelity/Pershing\n✅ Full transparency\n✅ No operational nightmare",
            "The data is clear: hedge fund net inflows hit $21B in Q1 2025. BlackRock is telling clients to increase allocations.\n\nThe RIAs who build alternatives capability now will define what a modern practice looks like.\n\nThe rest will spend years catching up.",
            "If you're an RIA thinking about alternatives, the playbook is simple:\n\n1. Allocate 10-20% to uncorrelated strategies\n2. Use a single vehicle (not 5 LP agreements)\n3. Integrate into existing custodial workflow\n\nLearn more: joinequi.com"
        ],

        email: `Subject: The data behind the 60/40 breakdown — and what to do about it\n\nHi [First Name],\n\nI wanted to share something that came up in a conversation with our CIO this week.\n\nIn 2022, the correlation between the S&P 500 and the Bloomberg Aggregate Bond Index hit 95%. For portfolios built on the assumption that stocks and bonds move in opposite directions, that's not just a bad year — it's a structural breakdown.\n\nThe advisors we're working with are solving this by adding 10-20% allocations to truly uncorrelated hedge fund strategies — and doing it through a single, operationally simple vehicle.\n\nI'd love to walk you through how this fits into your portfolio construction process. Would you have 20 minutes this week?\n\nBest,\nTory Burch\nCEO, Equi`
    },
    compliance: {
        linkedin: { passed: true, warnings: 0, flags: 0 },
        newsletter: { passed: true, warnings: 1, flags: 0 },
        twitter: { passed: true, warnings: 0, flags: 0 },
        email: { passed: true, warnings: 0, flags: 0 }
    },
    pieces: {
        linkedin: { id: 1 },
        newsletter: { id: 2 },
        twitter: { id: 3 },
        email: { id: 4 }
    }
};

const DEMO_VIDEO = {
    video: { segments: 12, word_count: 2847, topics: ["60/40 breakdown", "RIA infrastructure gap", "Multi-strategy allocation", "Tender offer fund", "Risk management"], duration_min: 32 },
    clips: [
        { title: "The 60/40 Correlation Bombshell", start_time: "01:24", end_time: "02:05", description: "Itay reveals the shocking 95% stock-bond correlation that broke traditional portfolios.", key_quote: "In 2022, the correlation between the S&P 500 and the Bloomberg Aggregate Bond Index hit 95%. That means your diversified portfolio was essentially a single bet.", platform_fit: ["linkedin", "twitter"] },
        { title: "The Three Barriers Every RIA Faces", start_time: "03:15", end_time: "04:22", description: "Itay breaks down why smart advisors can't access institutional hedge funds.", key_quote: "Access, diligence, and operations — none of these barriers are about the investment case. They're all infrastructure problems.", platform_fit: ["linkedin", "newsletter"] },
        { title: "The CIO Who Didn't Know Where to Start", start_time: "04:22", end_time: "04:48", description: "Tory shares a powerful anecdote from the Titan Investors roundtable.", key_quote: "A CIO of a $4 billion firm literally said 'I know I need this but I don't know where to start.' That's our pitch in one sentence.", platform_fit: ["twitter", "email"] },
        { title: "Why Fee Objections Miss the Point", start_time: "11:25", end_time: "12:20", description: "Itay reframes the fee conversation with compelling dispersion data.", key_quote: "The dispersion between top-quartile and bottom-quartile hedge fund managers is roughly 1,200 basis points per year. The value of manager selection in alternatives is 4 to 5 times greater than in traditional asset classes.", platform_fit: ["linkedin", "blog"] },
        { title: "Early Innings: The Decade-Long Opportunity", start_time: "15:10", end_time: "16:05", description: "Itay makes the case that RIA alternatives adoption is just getting started.", key_quote: "Independent RIAs allocate roughly 3 to 5% to alternatives. Institutional investors allocate 20 to 40%. That gap is going to close over the next decade.", platform_fit: ["twitter", "newsletter", "linkedin"] }
    ],
    blog: `# Why Multi-Strategy Hedge Fund Allocations Belong in Every RIA Portfolio\n\n## The 60/40 Assumption Is Broken\n\nFor decades, the 60/40 portfolio was the bedrock of financial planning. The logic was elegant: stocks provide growth, bonds provide ballast, and their negative correlation smooths the ride.\n\nThen 2022 happened.\n\nThe correlation between the S&P 500 and the Bloomberg Aggregate Bond Index hit 95%. Ninety-five percent. Your "diversified" portfolio was essentially a single bet. And this wasn't a one-month anomaly — the rolling 12-month correlation stayed above 60% for most of 2023.\n\nThe negative correlation that 60/40 relies on was a feature of a specific rate environment — ZIRP — and that environment is over.\n\n## The Infrastructure Gap\n\nHere's the paradox: most RIAs know they need alternatives exposure. Every advisor managing $2-10 billion for sophisticated, high-net-worth clients understands that the traditional playbook isn't enough.\n\nBut three barriers stand in the way:\n\n**Access.** The best multi-strategy managers have $5-10M minimums, sometimes higher. An RIA managing $3 billion across 500 client accounts can't practically allocate that way.\n\n**Diligence.** Evaluating hedge fund managers requires a fundamentally different skillset. You need to understand structural edge, risk management frameworks, operational infrastructure, and prime brokerage setups.\n\n**Operations.** Managing LP agreements, capital calls, K-1s, side pockets, and redemption queues across multiple hedge fund positions is an operational nightmare for firms built to run model portfolios.\n\n## The Endowment Model — Democratized\n\nYale, Harvard, and Stanford have allocated 25-40% to alternatives for two decades. Their returns have crushed traditional 60/40 benchmarks. But they have 50-person investment teams.\n\nThe question has always been: how does a five-person RIA get access to the same caliber of strategy?\n\nHistorically, the answer was "you can't." That's changing.\n\n## A New Approach\n\nThe tender offer fund structure represents a breakthrough for RIA access to hedge funds. As a registered 1940 Act fund, it provides:\n\n- **Diversified exposure** across multiple strategies and managers through a single allocation\n- **Quarterly liquidity** through tender offers — a major improvement over typical lock-ups\n- **Custodial compatibility** with Schwab, Fidelity, and Pershing\n- **Full transparency** — every position, every factor exposure, every risk metric\n\n## The Data Is Clear\n\nHedge fund industry net inflows were $21 billion in Q1 2025 — the strongest quarter in four years. BlackRock is telling institutional clients to increase allocations. Bridgewater's research shows a 20% alternatives allocation improved risk-adjusted returns by 150 basis points annualized over 15 years.\n\nThe advisors who build alternatives capability now will have a structural advantage for the next decade. The ones who wait will spend years trying to catch up.\n\n## Getting Started\n\nThe playbook is straightforward:\n\n1. **Allocate 10-20%** of client portfolios to truly uncorrelated strategies\n2. **Use a single vehicle** — not five separate LP agreements\n3. **Integrate** into existing portfolio construction and custodial workflows\n\nThe gap between institutional and independent advisor portfolios is closing. The question is whether you'll be leading that change or chasing it.`,
    social_posts: [
        { title: "The Correlation Wake-Up Call", platform: "linkedin", body: "In 2022, stock-bond correlation hit 95%. The 60/40 assumption is broken. Here's what institutional investors are doing that most RIAs aren't.", source: "Clip 1" },
        { title: "Three Barriers Thread", platform: "twitter", body: "Why can't most RIAs access institutional hedge funds? Three words: Access. Diligence. Operations. None of them are about the investment case.", source: "Clip 2" },
        { title: "The $4B CIO Quote", platform: "linkedin", body: "'I know I need this but I don't know where to start.' — CIO of a $4B RIA firm. This is the alternatives access gap in one sentence.", source: "Clip 3" },
        { title: "Fee Dispersion Insight", platform: "twitter", body: "Top-to-bottom quartile dispersion in hedge funds: 1,200 bps/year. In long-only equity: 200-300 bps. Manager selection matters 4-5x MORE in alternatives.", source: "Clip 4" },
        { title: "Early Innings Data Point", platform: "linkedin", body: "RIAs allocate 3-5% to alternatives. Institutions allocate 20-40%. That gap will close this decade. The RIAs moving now will define what modern practice looks like.", source: "Clip 5" },
        { title: "BlackRock Validates", platform: "twitter", body: "BlackRock just told clients to increase hedge fund allocations. $21B in net hedge fund inflows in Q1 2025. The institutional consensus is clear.", source: "Industry data" },
        { title: "Endowment Model Access", platform: "newsletter", body: "Yale and Harvard have run 25-40% alternatives for decades, crushing 60/40 returns. The barrier was always infrastructure — not conviction. That barrier is falling.", source: "Clips 4-5" },
        { title: "Operational Simplicity", platform: "linkedin", body: "One allocation. Quarterly liquidity. Works with your existing custodian. Full transparency. That's what institutional hedge fund access should look like for RIAs.", source: "Product overview" },
        { title: "The Decade Opportunity", platform: "email", body: "The structural tailwinds for RIA alternatives adoption are the strongest in a generation. Correlation shifts, channel growth, and technology enabling access.", source: "Clip 5" },
        { title: "Risk Management Edge", platform: "linkedin", body: "Real-time factor exposure monitoring. Equity beta caps at 0.25. Cross-manager correlation alerts. This is pension-fund-grade risk management — now available to independent RIAs.", source: "Risk section" },
        { title: "Conference Energy", platform: "twitter", body: "Just back from Titan Investors roundtable. Every advisor is thinking about alternatives access. The energy is palpable. The shift is real.", source: "Tory anecdote" }
    ],
    email_teaser: "This week on the Equi podcast: our CEO Tory and CIO Itay break down why the 60/40 portfolio assumption has fundamentally broken — and what the smartest RIAs are doing about it. Key insight: stock-bond correlation hit 95% in 2022. The solution isn't more of the same — it's truly uncorrelated hedge fund strategies, now accessible through a single allocation. Listen to the full conversation for the data, the playbook, and why we think this is the most interesting inflection point in alternatives investing in a generation.",
    calendar: {
        total_entries: 22,
        weeks: 3,
        start_date: "2026-04-01",
        end_date: "2026-04-21",
        entries: [
            { date: "2026-04-01", day: "Tue", time: "9:00 AM", platform: "linkedin", content_type: "Post", content_preview: "The 60/40 portfolio assumption is broken. In 2022, stock-bond correlation hit 95%..." },
            { date: "2026-04-01", day: "Tue", time: "12:00 PM", platform: "twitter", content_type: "Thread", content_preview: "🧵 The 60/40 portfolio assumption is dead. Here's why..." },
            { date: "2026-04-02", day: "Wed", time: "10:00 AM", platform: "newsletter", content_type: "Blurb", content_preview: "THE 60/40 PROBLEM — AND THE SOLUTION MOST RIAS ARE MISSING..." },
            { date: "2026-04-03", day: "Thu", time: "9:00 AM", platform: "linkedin", content_type: "Post", content_preview: "'I know I need this but I don't know where to start.' — CIO of a $4B RIA..." },
            { date: "2026-04-03", day: "Thu", time: "2:00 PM", platform: "email", content_type: "Snippet", content_preview: "Subject: The data behind the 60/40 breakdown..." },
            { date: "2026-04-04", day: "Fri", time: "11:00 AM", platform: "twitter", content_type: "Post", content_preview: "Top-to-bottom quartile dispersion in hedge funds: 1,200 bps/year..." },
            { date: "2026-04-07", day: "Mon", time: "9:00 AM", platform: "blog", content_type: "Article", content_preview: "Why Multi-Strategy Hedge Fund Allocations Belong in Every RIA Portfolio..." },
            { date: "2026-04-07", day: "Mon", time: "1:00 PM", platform: "linkedin", content_type: "Post", content_preview: "NEW on the blog: Why Multi-Strategy Hedge Fund Allocations Belong..." },
            { date: "2026-04-08", day: "Tue", time: "10:00 AM", platform: "twitter", content_type: "Thread", content_preview: "Why can't most RIAs access institutional hedge funds? Three words..." },
            { date: "2026-04-08", day: "Tue", time: "3:00 PM", platform: "email", content_type: "Teaser", content_preview: "This week on the Equi podcast: our CEO Tory and CIO Itay break down..." },
            { date: "2026-04-09", day: "Wed", time: "9:00 AM", platform: "linkedin", content_type: "Post", content_preview: "Real-time factor exposure monitoring. Equity beta caps at 0.25..." },
            { date: "2026-04-10", day: "Thu", time: "12:00 PM", platform: "twitter", content_type: "Post", content_preview: "BlackRock just told clients to increase hedge fund allocations..." },
            { date: "2026-04-10", day: "Thu", time: "4:00 PM", platform: "newsletter", content_type: "Feature", content_preview: "Yale and Harvard have run 25-40% alternatives for decades..." },
            { date: "2026-04-11", day: "Fri", time: "10:00 AM", platform: "linkedin", content_type: "Post", content_preview: "One allocation. Quarterly liquidity. Works with your existing custodian..." },
            { date: "2026-04-14", day: "Mon", time: "9:00 AM", platform: "twitter", content_type: "Thread", content_preview: "Just back from Titan Investors roundtable. Every advisor is thinking..." },
            { date: "2026-04-14", day: "Mon", time: "2:00 PM", platform: "linkedin", content_type: "Post", content_preview: "RIAs allocate 3-5% to alternatives. Institutions allocate 20-40%..." },
            { date: "2026-04-15", day: "Tue", time: "10:00 AM", platform: "email", content_type: "Follow-up", content_preview: "Following up on last week's note about the 60/40 breakdown..." },
            { date: "2026-04-16", day: "Wed", time: "9:00 AM", platform: "blog", content_type: "Case Study", content_preview: "How a $3B RIA Added Institutional Hedge Fund Exposure in 30 Days..." },
            { date: "2026-04-17", day: "Thu", time: "11:00 AM", platform: "twitter", content_type: "Post", content_preview: "The advisors who build alternatives capability now will define..." },
            { date: "2026-04-17", day: "Thu", time: "3:00 PM", platform: "linkedin", content_type: "Article", content_preview: "The fee objection in alternatives misses the point entirely..." },
            { date: "2026-04-18", day: "Fri", time: "9:00 AM", platform: "newsletter", content_type: "Recap", content_preview: "This week in alternatives: key developments in RIA adoption..." },
            { date: "2026-04-21", day: "Mon", time: "10:00 AM", platform: "linkedin", content_type: "Post", content_preview: "Week 3 recap: The response to our alternatives content has been..." }
        ]
    }
};

const DEMO_REVIEW = [
    { id: 1, platform: "linkedin", content_type: "linkedin_post", title: "Hedge Fund Access for RIAs", status: "review", created_at: new Date(Date.now() - 7200000).toISOString() },
    { id: 2, platform: "newsletter", content_type: "newsletter_blurb", title: "Q1 Alternatives Outlook", status: "review", created_at: new Date(Date.now() - 10800000).toISOString() },
    { id: 3, platform: "twitter", content_type: "twitter_thread", title: "60/40 Correlation Thread", status: "review", created_at: new Date(Date.now() - 14400000).toISOString() },
];

const DEMO_CALENDAR = [
    { platform: "linkedin", content_type: "Post", scheduled_date: "2026-04-01", scheduled_time: "9:00 AM", content_preview: "The 60/40 portfolio assumption is broken...", status: "scheduled" },
    { platform: "twitter", content_type: "Thread", scheduled_date: "2026-04-01", scheduled_time: "12:00 PM", content_preview: "🧵 The 60/40 portfolio assumption is dead...", status: "scheduled" },
    { platform: "newsletter", content_type: "Blurb", scheduled_date: "2026-04-02", scheduled_time: "10:00 AM", content_preview: "THE 60/40 PROBLEM — AND THE SOLUTION...", status: "scheduled" },
    { platform: "linkedin", content_type: "Post", scheduled_date: "2026-04-03", scheduled_time: "9:00 AM", content_preview: "'I know I need this but I don't know where to start'...", status: "draft" },
    { platform: "email", content_type: "Snippet", scheduled_date: "2026-04-03", scheduled_time: "2:00 PM", content_preview: "Subject: The data behind the 60/40 breakdown...", status: "draft" },
];

// Intercept all fetch calls
const originalFetch = window.fetch;
window.fetch = async function(url, options = {}) {
    const path = typeof url === 'string' ? url : url.toString();

    if (path === '/api/dashboard') return mockResponse(DEMO_DASHBOARD);
    if (path === '/api/review') return mockResponse(DEMO_REVIEW);
    if (path.startsWith('/api/calendar')) return mockResponse(DEMO_CALENDAR);
    if (path.startsWith('/api/content?')) return mockResponse([]);

    if (path === '/api/generate' && options.method === 'POST') {
        await fakeDelay(1500);
        return mockResponse(DEMO_GENERATE);
    }

    if (path === '/api/process-video' && options.method === 'POST') {
        await fakeDelay(2000);
        return mockResponse(DEMO_VIDEO);
    }

    if (path.match(/\/api\/content\/\d+\/status/) && options.method === 'PUT') {
        return mockResponse({ ok: true });
    }

    if (path.match(/\/api\/content\/\d+$/)) {
        return mockResponse({ id: 1, platform: "linkedin", title: "Demo Content", body: DEMO_GENERATE.content.linkedin, status: "review", compliance_notes: "" });
    }

    return originalFetch.apply(this, arguments);
};

// Intercept XMLHttpRequest for file upload (XHR-based upload with progress)
const OriginalXHR = window.XMLHttpRequest;
class MockXHR extends OriginalXHR {
    constructor() {
        super();
        this._mockUrl = null;
        this._mockMethod = null;
    }

    open(method, url, ...args) {
        this._mockUrl = url;
        this._mockMethod = method;
        if (url === '/api/process-video-upload' && method === 'POST') {
            // We'll intercept in send()
            return super.open(method, url, ...args);
        }
        return super.open(method, url, ...args);
    }

    send(body) {
        if (this._mockUrl === '/api/process-video-upload' && this._mockMethod === 'POST') {
            // Simulate upload progress
            const self = this;

            // Simulate upload progress events
            let progress = 0;
            const uploadInterval = setInterval(() => {
                progress += 20;
                if (progress > 100) progress = 100;
                const evt = new ProgressEvent('progress', {
                    lengthComputable: true,
                    loaded: progress,
                    total: 100
                });
                if (self.upload && self.upload.dispatchEvent) {
                    self.upload.dispatchEvent(evt);
                }
                if (progress >= 100) {
                    clearInterval(uploadInterval);
                    // Fire upload 'load' event
                    const loadEvt = new ProgressEvent('load', { lengthComputable: true, loaded: 100, total: 100 });
                    if (self.upload && self.upload.dispatchEvent) {
                        self.upload.dispatchEvent(loadEvt);
                    }

                    // Simulate transcription delay, then respond
                    setTimeout(() => {
                        // Add video_file_id and clip_file to demo response
                        const uploadResponse = JSON.parse(JSON.stringify(DEMO_VIDEO));
                        uploadResponse.video_file_id = 'demo_upload_001';
                        uploadResponse.clips = uploadResponse.clips.map((clip, i) => ({
                            ...clip,
                            clip_file: `demo_clip_${i + 1}.mp4`
                        }));

                        Object.defineProperty(self, 'status', { value: 200, writable: false, configurable: true });
                        Object.defineProperty(self, 'responseText', { value: JSON.stringify(uploadResponse), writable: false, configurable: true });

                        self.dispatchEvent(new Event('load'));
                    }, 2500);
                }
            }, 300);

            return; // Don't actually send
        }
        return super.send(body);
    }
}
window.XMLHttpRequest = MockXHR;

function mockResponse(data) {
    return new Response(JSON.stringify(data), {
        status: 200,
        headers: { 'Content-Type': 'application/json' }
    });
}

function fakeDelay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

console.log('🎭 Demo mode active — using mock data');
