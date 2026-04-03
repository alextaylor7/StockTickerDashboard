// Clientside callbacks: window.dash_clientside.stock_ticker.* (see ClientsideFunction in Python)
window.dash_clientside = window.dash_clientside || {};
window.dash_clientside.stock_ticker = {
    plotlyResizeHook: function (_pathname) {
        if (window.__stockTickerPlotlyResizeHook) {
            return window.dash_clientside.no_update;
        }
        function resizeAllPlotly() {
            if (!window.Plotly || !window.Plotly.Plots) return;
            document.querySelectorAll(".js-plotly-plot").forEach(function (gd) {
                try {
                    window.Plotly.Plots.resize(gd);
                } catch (e) {
                }
            });
        }
        function scheduleResize() {
            window.requestAnimationFrame(resizeAllPlotly);
        }
        window.addEventListener("resize", scheduleResize);
        window.addEventListener("load", function () {
            setTimeout(scheduleResize, 150);
        });
        document.addEventListener("visibilitychange", function () {
            if (!document.hidden) setTimeout(scheduleResize, 150);
        });
        if (window.ResizeObserver) {
            var shell = document.getElementById("dash-shell");
            if (shell) {
                new ResizeObserver(function () {
                    scheduleResize();
                }).observe(shell);
            }
        }
        setTimeout(scheduleResize, 400);
        setTimeout(scheduleResize, 1200);
        window.__stockTickerPlotlyResizeHook = true;
        return 1;
    },

    sessionLoadClick: function (n_clicks) {
        if (!n_clicks) {
            return window.dash_clientside.no_update;
        }
        var el = document.getElementById("session-upload");
        if (el) {
            var inp = el.querySelector('input[type="file"]');
            if (inp) {
                inp.click();
            }
        }
        return n_clicks;
    },
};
