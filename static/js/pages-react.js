(function () {
    const root = document.getElementById("reactPageRoot");
    const stateTag = document.getElementById("reactPageState");

    if (!root || !stateTag || !window.React || !window.ReactDOM) {
        return;
    }

    const h = React.createElement;
    let state = {};

    try {
        state = JSON.parse(stateTag.textContent || "{}");
    } catch (error) {
        state = {};
    }

    const page = state.page || "";

    const renderAuthHeading = function (titleText) {
        return h(
            "div",
            { style: { width: "min(100%, 440px)", textAlign: "center", marginBottom: "18px" } },
            h(
                "h1",
                {
                    style: {
                        margin: 0,
                        fontFamily: "'Montserrat', sans-serif",
                        fontSize: "clamp(1.3rem, 3vw, 1.8rem)",
                        letterSpacing: "0.04em"
                    }
                },
                titleText
            )
        );
    };

    const formatStatus = function (value) {
        return String(value || "idle")
            .replace(/_/g, " ")
            .replace(/\b\w/g, function (m) { return m.toUpperCase(); });
    };

    const pages = {
        login: function () {
            return h(
                React.Fragment,
                null,
                renderAuthHeading("AI Video To Blog Summarizer"),
                h(
                    "section",
                    { className: "auth-card" },
                    h("h1", { className: "auth-title" }, "User Login"),
                    h("p", { className: "auth-subtitle" }, "Sign in to upload videos, generate summaries, and turn your content into blog-ready articles."),
                    h(
                        "form",
                        { method: "POST", className: "auth-form" },
                        h(
                            "div",
                            { className: "field-stack" },
                            h(
                                "label",
                                { className: "pill-field" },
                                h("span", { className: "field-icon", "aria-hidden": "true" }, h("span", null, "\u25CF")),
                                h("input", { name: "email", type: "email", placeholder: "Username or email", defaultValue: state.email || "", required: true })
                            ),
                            h(
                                "label",
                                { className: "pill-field trailing-icon" },
                                h("input", { name: "password", type: "password", placeholder: "Password", required: true }),
                                h("span", { className: "field-icon", "aria-hidden": "true" }, h("span", null, "\u25CF"))
                            )
                        ),
                        h("div", { className: "auth-actions" }, h("button", { type: "submit", className: "btn-primary", style: { width: "100%" } }, "Login")),
                        h("a", { href: "/auth/google", className: "btn-secondary", style: { width: "100%" } }, "Continue with Google")
                    ),
                    h(
                        "div",
                        { className: "auth-links" },
                        h("a", { href: "/forgot-password", className: "ghost-link" }, "Forgot password?"),
                        h("a", { href: "/register", className: "ghost-link" }, "Don't have one signup")
                    )
                )
            );
        },
        register: function () {
            return h(
                "section",
                { className: "auth-card" },
                h("p", { className: "auth-eyebrow" }, "New account"),
                h("h1", { className: "auth-title" }, "Create Access"),
                h("p", { className: "auth-subtitle" }, "Set up your workspace to summarize long videos and generate blog content with a single flow."),
                h(
                    "form",
                    { method: "POST", className: "auth-form" },
                    h(
                        "div",
                        { className: "field-stack" },
                        h(
                            "label",
                            { className: "pill-field" },
                            h("span", { className: "field-icon", "aria-hidden": "true" }, h("span", null, "\u25CF")),
                            h("input", { name: "email", type: "email", placeholder: "Email address", defaultValue: state.email || "", required: true })
                        ),
                        h(
                            "label",
                            { className: "pill-field trailing-icon" },
                            h("input", { name: "password", type: "password", placeholder: "Password (min 8 characters)", required: true }),
                            h("span", { className: "field-icon", "aria-hidden": "true" }, h("span", null, "\u25CF"))
                        )
                    ),
                    h("button", { type: "submit", className: "btn-primary", style: { width: "100%" } }, "Register")
                ),
                h("div", { className: "auth-links" }, h("a", { href: "/", className: "ghost-link" }, "Back to login"))
            );
        },
        forgot_password: function () {
            return h(
                "section",
                { className: "auth-card" },
                h("p", { className: "auth-eyebrow" }, "Password help"),
                h("h1", { className: "auth-title" }, "Reset Access"),
                h("p", { className: "auth-subtitle" }, "Enter the email tied to your account and we will generate a fresh password reset link."),
                h(
                    "form",
                    { method: "POST", className: "auth-form" },
                    h(
                        "label",
                        { className: "pill-field" },
                        h("span", { className: "field-icon", "aria-hidden": "true" }, h("span", null, "@")),
                        h("input", { name: "email", type: "email", placeholder: "Enter your account email", required: true })
                    ),
                    h("button", { type: "submit", className: "btn-primary", style: { width: "100%" } }, "Create reset link")
                ),
                state.reset_link
                    ? h(
                        "div",
                        { className: "content-panel reset-link-panel", style: { marginTop: "22px" } },
                        h("h2", { className: "section-title" }, "Reset link"),
                        h("p", { className: "card-copy" }, "Open this link to set a new password."),
                        h("a", { href: state.reset_link, className: "inline-link" }, state.reset_link)
                    )
                    : null,
                h("div", { className: "auth-links" }, h("a", { href: "/", className: "ghost-link" }, "Back to login"))
            );
        },
        reset_password: function () {
            return h(
                "section",
                { className: "auth-card" },
                h("p", { className: "auth-eyebrow" }, "Secure update"),
                h("h1", { className: "auth-title" }, "New Password"),
                h("p", { className: "auth-subtitle" }, "Choose a strong password you have not used before and confirm it to finish the reset."),
                h(
                    "form",
                    { method: "POST", className: "auth-form" },
                    h(
                        "div",
                        { className: "field-stack" },
                        h(
                            "label",
                            { className: "pill-field trailing-icon" },
                            h("input", { name: "password", type: "password", placeholder: "New password", required: true }),
                            h("span", { className: "field-icon", "aria-hidden": "true" }, h("span", null, "\u25CF"))
                        ),
                        h(
                            "label",
                            { className: "pill-field trailing-icon" },
                            h("input", { name: "confirm_password", type: "password", placeholder: "Confirm new password", required: true }),
                            h("span", { className: "field-icon", "aria-hidden": "true" }, h("span", null, "\u25CF"))
                        )
                    ),
                    h("button", { type: "submit", className: "btn-primary", style: { width: "100%" } }, "Update password")
                ),
                h("div", { className: "auth-links" }, h("a", { href: "/", className: "ghost-link" }, "Back to login"))
            );
        },
        upload: function () {
            const [submitting, setSubmitting] = React.useState(false);

            return h(
                "section",
                { className: "two-column" },
                h(
                    "div",
                    { className: "content-panel" },
                    h(
                        "div",
                        { className: "section-header" },
                        h(
                            "div",
                            null,
                            h("p", { className: "auth-eyebrow" }, "Input"),
                            h("h1", { className: "section-title" }, "Upload Video"),
                            h("p", { className: "section-subtitle" }, "Choose a file or paste a public video URL. Either option will start the same processing flow.")
                        )
                    ),
                    h(
                        "form",
                        {
                            method: "POST",
                            encType: "multipart/form-data",
                            className: "surface-form",
                            onSubmit: function () { setSubmitting(true); }
                        },
                        h(
                            "label",
                            { className: "surface-label" },
                            "Video file",
                            h("span", { className: "file-input-shell" }, h("input", { type: "file", name: "video" }))
                        ),
                        h(
                            "label",
                            { className: "surface-label" },
                            "Video URL",
                            h("input", { className: "surface-input", name: "video_url", placeholder: "https://example.com/video.mp4 or https://www.youtube.com/watch?v=..." })
                        ),
                        h(
                            "div",
                            { className: "button-row" },
                            h("button", { type: "submit", className: "btn-primary", disabled: submitting }, submitting ? "Starting..." : "Process video"),
                            h("a", { href: "/dashboard", className: "btn-secondary" }, "Back to dashboard")
                        )
                    )
                ),
                h(
                    "aside",
                    { className: "stat-panel" },
                    h("div", { className: "stat-block" }, h("span", { className: "auth-eyebrow" }, "How it works"), h("strong", null, "1. Upload source"), h("p", { className: "card-copy" }, "You can provide either a local file or a public video URL.")),
                    h("div", { className: "stat-block" }, h("strong", null, "2. Wait for transcript"), h("p", { className: "card-copy" }, "The job moves through download, extraction, Faster-Whisper transcription, and model selection.")),
                    h("div", { className: "stat-block" }, h("strong", null, "3. Export content"), h("p", { className: "card-copy" }, "Open the generated summary, create the blog article, and download either as PDF."))
                )
            );
        },
        history: function () {
            const jobs = Array.isArray(state.jobs) ? state.jobs : [];

            return h(
                "section",
                { className: "table-panel" },
                h(
                    "div",
                    { className: "section-header" },
                    h(
                        "div",
                        null,
                        h("p", { className: "auth-eyebrow" }, "Archive"),
                        h("h1", { className: "section-title" }, "Your Video History"),
                        h("p", { className: "section-subtitle" }, "Review status, model choices, and downloadable outputs for all previous jobs.")
                    ),
                    h("a", { href: "/upload", className: "btn-secondary" }, "New upload")
                ),
                h(
                    "div",
                    { className: "table-wrap" },
                    h(
                        "table",
                        null,
                        h(
                            "thead",
                            null,
                            h(
                                "tr",
                                null,
                                h("th", null, "Video"),
                                h("th", null, "Status"),
                                h("th", null, "Transcription"),
                                h("th", null, "Model"),
                                h("th", null, "Summary"),
                                h("th", null, "Blog")
                            )
                        ),
                        h(
                            "tbody",
                            null,
                            jobs.length
                                ? jobs.map(function (job) {
                                    return h(
                                        "tr",
                                        { key: job.job_id || job.file },
                                        h("td", null, job.file || ""),
                                        h("td", null, h("span", { className: "status-pill" }, formatStatus(job.status))),
                                        h("td", null, job.transcription_provider || "whisper"),
                                        h("td", null, job.summary_model || "-"),
                                        h(
                                            "td",
                                            null,
                                            job.summary_file
                                                ? h(
                                                    "div",
                                                    { className: "chip-row" },
                                                    h("a", { className: "chip-button", href: "/summary/" + encodeURIComponent(job.job_id) }, "View"),
                                                    h("a", { className: "chip-button", href: "/download_summary/" + encodeURIComponent(job.job_id) }, "Download")
                                                )
                                                : h("span", { className: "meta-text" }, "Pending")
                                        ),
                                        h(
                                            "td",
                                            null,
                                            job.status === "blog_ready"
                                                ? h(
                                                    "div",
                                                    { className: "chip-row" },
                                                    h("a", { className: "chip-button", href: "/blog/" + encodeURIComponent(job.job_id) }, "View"),
                                                    h("a", { className: "chip-button", href: "/download_blog/" + encodeURIComponent(job.job_id) }, "Download")
                                                )
                                                : h("span", { className: "meta-text" }, "Pending")
                                        )
                                    );
                                })
                                : h("tr", null, h("td", { colSpan: 6 }, h("div", { className: "empty-state" }, "No jobs yet. Upload your first video to start building summaries and blogs.")))
                        )
                    )
                )
            );
        },
        select_model: function () {
            const options = Array.isArray(state.summary_model_options) ? state.summary_model_options : [];
            const title = state.job_title || state.job_id || "";

            return h(
                "section",
                { className: "two-column" },
                h(
                    "div",
                    { className: "content-panel" },
                    h("p", { className: "auth-eyebrow" }, "Model selection"),
                    h("h1", { className: "section-title" }, "Choose a summarization model"),
                    h("p", { className: "section-subtitle select-model-subtitle" }, "Video name: ", h("strong", null, title)),
                    h("p", { className: "section-subtitle" }, "Pick the model you want for your video.Once selected, click generate summary."),
                    h(
                        "form",
                        { method: "POST", className: "surface-form" },
                        h("div", null, h("h2", { className: "card-title" }, "Summary Model")),
                        h(
                            "div",
                            { className: "choice-grid" },
                            options.map(function (option) {
                                const disabled = !option.enabled;
                                const className = "choice-card" + (disabled ? " choice-card-disabled" : "");
                                return h(
                                    "label",
                                    { className: className, key: option.value },
                                    h("input", { type: "radio", name: "model", value: option.value, defaultChecked: Boolean(option.checked), disabled: disabled }),
                                    h("span", null, h("strong", null, option.label), h("span", { className: "card-copy" }, option.description))
                                );
                            })
                        ),
                        h(
                            "div",
                            { className: "button-row" },
                            h("button", { type: "submit", className: "btn-primary" }, "Generate Summary"),
                            h("a", { href: "/cleaned_transcript/" + encodeURIComponent(state.job_id), className: "btn-secondary" }, "View Cleaned Transcript"),
                            h("a", { href: "/dashboard?job_id=" + encodeURIComponent(state.job_id), className: "btn-secondary" }, "Back to dashboard")
                        )
                    )
                )
            );
        },
        summary: function () {
            return h(
                "section",
                { className: "content-panel" },
                h(
                    "div",
                    { className: "section-header" },
                    h(
                        "div",
                        null,
                        h("p", { className: "auth-eyebrow" }, "Output"),
                        h("h1", { className: "section-title" }, "Generated Summary"),
                        h("p", { className: "section-subtitle" }, "Review the summary or generate a blog")
                    ),
                    h("div", { className: "tag-row" }, h("span", { className: "tag" }, "Model: " + String(state.model_name || "").toUpperCase()), h("span", { className: "tag" }, "Video: " + (state.display_name || "")))
                ),
                h("div", { className: "text-content", style: { marginTop: "22px" } }, state.summary || ""),
                state.timestamp_summary
                    ? h(
                        "div",
                        { style: { marginTop: "28px" } },
                        h("div", { className: "section-header", style: { marginBottom: "12px" } }, h("div", null, h("p", { className: "auth-eyebrow" }, "Timeline"), h("h2", { className: "card-title" }, "Timestamp Summary"))),
                        h("div", { className: "text-content" }, state.timestamp_summary)
                    )
                    : null,
                h("div", { className: "action-row", style: { marginTop: "28px" } }, h("a", { className: "btn-primary", href: "/download_summary/" + encodeURIComponent(state.job_id) }, "Download Summary"))
            );
        },
        blog: function () {
            return h(
                "section",
                { className: "content-panel" },
                h(
                    "div",
                    { className: "section-header" },
                    h("div", null, h("p", { className: "auth-eyebrow" }, "Output"), h("h1", { className: "section-title" }, "Generated Blog")),
                    h("div", { className: "tag-row" }, h("span", { className: "tag" }, "Model: " + String(state.model_name || "").toUpperCase()), h("span", { className: "tag" }, "Video: " + (state.display_name || "")))
                ),
                h("div", { className: "text-content", style: { marginTop: "22px" } }, state.blog || ""),
                h("div", { className: "action-row", style: { marginTop: "28px" } }, h("a", { className: "btn-primary", href: "/download_blog/" + encodeURIComponent(state.job_id) }, "Download Blog"))
            );
        },
        cleaned_transcript: function () {
            return h(
                "section",
                { className: "content-panel" },
                h(
                    "div",
                    { className: "section-header" },
                    h("div", null, h("p", { className: "auth-eyebrow" }, "Transcript"), h("h1", { className: "section-title" }, "Cleaned Transcript"), h("p", { className: "section-subtitle" }, "Video name: ", h("strong", null, state.job_title || state.job_id || "")))
                ),
                h("div", { className: "text-content", style: { marginTop: "22px" } }, state.cleaned_transcript || ""),
                h("div", { className: "action-row", style: { marginTop: "28px" } }, h("a", { className: "btn-secondary", href: "/select_model/" + encodeURIComponent(state.job_id) }, "Back to Select Model"))
            );
        },
    };

    const renderer = pages[page];
    if (!renderer) {
        return;
    }

    ReactDOM.createRoot(root).render(h(renderer));
})();
