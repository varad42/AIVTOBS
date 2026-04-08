(function () {
    const rootElement = document.getElementById("dashboardReactRoot");
    const stateElement = document.getElementById("dashboardInitialState");

    if (!rootElement || !stateElement || !window.React || !window.ReactDOM) {
        return;
    }

    const h = React.createElement;
    let initialState = {};

    try {
        initialState = JSON.parse(stateElement.textContent || "{}");
    } catch (error) {
        initialState = {};
    }

    const formatStatusLabel = function (status) {
        return (status || "idle")
            .replace(/_/g, " ")
            .replace(/\b\w/g, function (ch) { return ch.toUpperCase(); });
    };

    const formatSourceLabel = function (sourceType) {
        if (sourceType === "youtube") {
            return "YouTube";
        }

        if (sourceType === "local") {
            return "Upload";
        }

        return "External";
    };

    const getJobTitle = function (job) {
        return job.display_name || job.job_slug || job.job_id || "Untitled job";
    };

    const getJobDateLabel = function (job) {
        const rawDate = job.uploaded_at || job.queued_at;
        if (!rawDate) {
            return "Waiting for timestamp";
        }

        const parsed = new Date(rawDate);
        if (Number.isNaN(parsed.getTime())) {
            return String(rawDate).replace("T", " ").slice(0, 16);
        }

        return parsed.toLocaleString();
    };

    const getShortJobId = function (jobId) {
        return String(jobId || "").slice(0, 8);
    };

    const stageSteps = [
        { label: "Uploaded", threshold: 15 },
        { label: "Downloaded", threshold: 20 },
        { label: "Transcribed", threshold: 60 },
        { label: "Ready for model", threshold: 80 },
        { label: "Complete", threshold: 100 },
    ];

    function DashboardApp() {
        const [submitting, setSubmitting] = React.useState(false);

        const jobs = Array.isArray(initialState.jobs) ? initialState.jobs : [];
        const activeJob = initialState.active_job || null;
        const activeProgress = Number(initialState.active_progress || 0);
        const activeStatus = (activeJob && activeJob.status) || "idle";
        const activeStatusLabel = formatStatusLabel(initialState.active_status_label || activeStatus);
        const currentSource = activeJob ? formatSourceLabel(activeJob.source_type) : "Upload";
        const activeTitle = activeJob ? getJobTitle(activeJob) : "";
        const summaryReadyCount = Number(initialState.summary_ready_count || 0);
        const blogReadyCount = Number(initialState.blog_ready_count || 0);
        const userEmail = initialState.user_email || "";

        const onSubmit = function () {
            setSubmitting(true);
        };

        return h(
            "section",
            { className: "dashboard-shell dashboard-shell-modern" },
            h(
                "aside",
                { className: "dashboard-sidebar panel dashboard-sidebar-modern", id: "dashboardSidebar" },
                h(
                    "div",
                    { className: "sidebar-header dashboard-sidebar-header" },
                    h(
                        "div",
                        null,
                        h("p", { className: "auth-eyebrow" }, "Workspace"),
                        h("h2", { className: "card-title" }, "History")
                    )
                ),
                h(
                    "div",
                    { className: "dashboard-sidebar-top" },
                    h(
                        "div",
                        { className: "account-card history-account-card dashboard-profile-card" },
                        h(
                            "div",
                            { className: "dashboard-profile-top" },
                            h("div", { className: "dashboard-avatar", "aria-hidden": "true" }, userEmail ? userEmail[0].toUpperCase() : "U"),
                            h(
                                "div",
                                { className: "dashboard-profile-copy" },
                                h("p", { className: "auth-eyebrow" }, "Signed in"),
                                h("strong", null, userEmail),
                                h("span", { className: "meta-text" }, "Studio workspace active")
                            )
                        ),
                        h("a", { href: "/logout", className: "btn-secondary dashboard-sidebar-logout" }, "Logout")
                    ),
                    h("a", { href: "/dashboard?new_chat=1", className: "btn-primary dashboard-new-chat" }, "+ New Chat")
                ),
                h(
                    "div",
                    { className: "metric-list dashboard-sidebar-metrics" },
                    h("article", { className: "metric" }, h("span", null, "Summaries"), h("strong", null, summaryReadyCount)),
                    h("article", { className: "metric" }, h("span", null, "Blogs"), h("strong", null, blogReadyCount))
                ),
                h("div", { className: "dashboard-history-header" }, h("p", { className: "auth-eyebrow" }, "Recent Jobs")),
                h(
                    "div",
                    { className: "sidebar-section sidebar-scroll dashboard-history-list" },
                    jobs.length
                        ? jobs.map(function (job) {
                            const status = job.status || "idle";
                            const source = formatSourceLabel(job.source_type);
                            const isActive = Boolean(activeJob && activeJob.job_id === job.job_id);
                            const cardClass = "history-mini-card history-studio-card" + (isActive ? " history-studio-card-active" : "");

                            return h(
                                "a",
                                { href: "/dashboard?job_id=" + encodeURIComponent(job.job_id), className: "history-job-link", key: job.job_id },
                                h(
                                    "article",
                                    { className: cardClass },
                                    h(
                                        "div",
                                        { className: "history-studio-head" },
                                        h(
                                            "span",
                                            { className: "status-pill dashboard-status-chip status-" + status },
                                            formatStatusLabel(status)
                                        ),
                                        h("span", { className: "history-studio-source" }, source)
                                    ),
                                    h("h3", null, getJobTitle(job)),
                                    h(
                                        "div",
                                        { className: "history-mini-meta history-studio-meta" },
                                        h("span", null, getJobDateLabel(job)),
                                        h("span", null, "ID " + getShortJobId(job.job_id))
                                    )
                                )
                            );
                        })
                        : h(
                            "div",
                            { className: "empty-state dashboard-history-empty" },
                            h("strong", null, "No history yet"),
                            h("span", null, "Your uploads, summaries, and blogs will appear here as a running studio archive.")
                        )
                )
            ),
            h(
                "div",
                { className: "workspace-stack dashboard-workspace-modern" },
                h(
                    "section",
                    { className: "content-panel dashboard-hero-panel", id: "upload-studio" },
                    h(
                        "div",
                        { className: "dashboard-hero-copy" },
                        h("p", { className: "auth-eyebrow" }, "AI Video Studio"),
                        h(
                            "div",
                            { className: "dashboard-hero-ball-wrap", "aria-hidden": "true" },
                            h(
                                "video",
                                {
                                    className: "dashboard-hero-ball-video",
                                    autoPlay: true,
                                    muted: true,
                                    loop: true,
                                    playsInline: true,
                                    preload: "auto"
                                },
                                h("source", { src: "/static/media/dashboard-ball.mp4", type: "video/mp4" })
                            )
                        ),
                        h(
                            "p",
                            { className: "hero-copy dashboard-hero-subtitle" },
                            "Drop in a local file or paste a YouTube link. The studio handles the pipeline and keeps the current job visible while it works."
                        )
                    ),
                    h(
                        "div",
                        { className: "dashboard-hero-actions" },
                        h(
                            "div",
                            { className: "dashboard-mode-pills" },
                            h("span", { className: "tag dashboard-mode-pill" }, "Local Upload"),
                            h("span", { className: "tag dashboard-mode-pill" }, "YouTube Link")
                        )
                    ),
                    h(
                        "form",
                        {
                            method: "POST",
                            action: "/upload",
                            encType: "multipart/form-data",
                            className: "surface-form dashboard-composer",
                            id: "dashboardUploadForm",
                            onSubmit: onSubmit
                        },
                        h(
                            "div",
                            { className: "dashboard-composer-grid" },
                            h(
                                "label",
                                { className: "surface-label dashboard-dropzone" },
                                h("span", { className: "dashboard-dropzone-title" }, "Upload a video file"),
                                h("span", { className: "dashboard-dropzone-copy" }, "Choose MP4, MOV, or another video file from your device."),
                                h(
                                    "span",
                                    { className: "file-input-shell dashboard-file-shell" },
                                    h("input", { type: "file", name: "video" })
                                )
                            ),
                            h(
                                "label",
                                { className: "surface-label dashboard-url-block" },
                                h("span", { className: "dashboard-dropzone-title" }, "Paste a YouTube URL"),
                                h("span", { className: "dashboard-dropzone-copy" }, "Use any public YouTube link and let the worker fetch the transcript or video."),
                                h("input", { className: "surface-input dashboard-url-input", name: "video_url", placeholder: "https://www.youtube.com/watch?v=..." })
                            )
                        ),
                        h(
                            "div",
                            { className: "button-row dashboard-composer-actions" },
                            h(
                                "button",
                                { type: "submit", className: "btn-primary dashboard-process-button", disabled: submitting },
                                submitting ? "Starting..." : "Process Video"
                            ),
                            h("a", { href: "/dashboard?new_chat=1", className: "btn-secondary" }, "Reset Composer")
                        )
                    )
                ),
                h(
                    "section",
                    { className: "content-panel dashboard-current-panel" },
                    h(
                        "div",
                        { className: "section-header dashboard-current-header" },
                        h(
                            "div",
                            null,
                            h("p", { className: "auth-eyebrow" }, "Current Job"),
                            h("h2", { className: "section-title" }, "Live Processing Studio"),
                            h("p", { className: "section-subtitle" }, "Track the selected job, see its current stage, and jump into the next available action.")
                        ),
                        h("span", { className: "status-pill dashboard-status-chip status-" + activeStatus }, activeStatusLabel)
                    ),
                    activeJob
                        ? h(
                            "div",
                            { className: "dashboard-current-grid" },
                            h(
                                "div",
                                { className: "dashboard-preview-shell" },
                                activeJob.source_type === "youtube" && activeJob.youtube_video_id
                                    ? h("img", {
                                        className: "media-preview dashboard-current-preview",
                                        src: "/youtube_thumbnail/" + encodeURIComponent(activeJob.youtube_video_id),
                                        alt: "YouTube thumbnail preview"
                                    })
                                    : h(
                                        "div",
                                        { className: "dashboard-preview-placeholder" },
                                        h("span", { className: "dashboard-preview-icon", "aria-hidden": "true" }, "\u25B6"),
                                        h("strong", null, currentSource),
                                        h("span", null, activeTitle)
                                    )
                            ),
                            h(
                                "div",
                                { className: "dashboard-current-copy" },
                                h(
                                    "div",
                                    { className: "dashboard-current-meta" },
                                    h("span", { className: "tag dashboard-mode-pill" }, currentSource),
                                    h("span", { className: "meta-text" }, "Job ID " + getShortJobId(activeJob.job_id))
                                ),
                                h("h3", { className: "card-title dashboard-current-title" }, activeTitle),
                                h("p", { className: "card-copy dashboard-current-text" }, "The studio keeps this card focused on the selected job so you can upload, monitor progress, and open the next step without leaving the dashboard."),
                                h(
                                    "div",
                                    { className: "dashboard-progress-card" },
                                    h(
                                        "div",
                                        { className: "section-header dashboard-progress-header" },
                                        h("span", { className: "card-title" }, "Progress"),
                                        h("span", { className: "dashboard-progress-value" }, activeProgress + "%")
                                    ),
                                    h("div", { className: "pill-progress dashboard-progress-bar" }, h("span", { style: { width: activeProgress + "%" } }))
                                ),
                                h(
                                    "div",
                                    { className: "dashboard-stage-list" },
                                    stageSteps.map(function (stage) {
                                        const stageClass = "dashboard-stage-item" + (activeProgress >= stage.threshold ? " is-complete" : "");
                                        return h("div", { className: stageClass, key: stage.label }, stage.label);
                                    })
                                ),
                                h(
                                    "div",
                                    { className: "action-row dashboard-action-dock" },
                                    activeJob.status === "waiting_for_model" ? h("a", { className: "btn-primary", href: "/select_model/" + encodeURIComponent(activeJob.job_id) }, "Select Model") : null,
                                    activeJob.summary_file ? h("a", { className: "btn-secondary", href: "/summary/" + encodeURIComponent(activeJob.job_id) }, "View Summary") : null,
                                    activeJob.summary_file && !activeJob.blog_file && activeJob.status !== "blog_requested"
                                        ? h("a", { className: "btn-secondary", href: "/generate_blog/" + encodeURIComponent(activeJob.job_id) }, "Generate Blog")
                                        : null,
                                    activeJob.blog_file ? h("a", { className: "btn-secondary", href: "/blog/" + encodeURIComponent(activeJob.job_id) }, "View Blog") : null
                                )
                            )
                        )
                        : h(
                            "div",
                            { className: "dashboard-empty-studio" },
                            h(
                                "div",
                                { className: "dashboard-empty-visual", "aria-hidden": "true" },
                                h("span", null, "\u25EF"),
                                h("span", null, "\u25B6"),
                                h("span", null, "\u271A")
                            ),
                            h(
                                "div",
                                { className: "dashboard-empty-copy" },
                                h("p", { className: "auth-eyebrow" }, "Ready"),
                                h("h3", { className: "card-title" }, "Start a new upload session"),
                                h("p", { className: "section-subtitle" }, "Your composer is reset and ready. Add a file or YouTube URL above to begin a fresh job.")
                            )
                        )
                )
            )
        );
    }

    const root = ReactDOM.createRoot(rootElement);
    root.render(h(DashboardApp));
})();
