/*
 * Pyxis Effector - Plugin for Aegisub
 * Copyright (C) 2026 @mandholine, @effector2, @pholguinc
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation version 3.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program. If not, see <https://www.gnu.org/licenses/>.
 * For any question you can visit: https://discord.gg/fsxRESeQZN
 */

/**
 * @file bug_report.js
 * @description Issue reporting and diagnostic telemetry collection dialogue for Pyxis Effector.
 * Handles screenshot attachment, log packaging, backend submission, and community hub links.
 * @module PyxisBugReport
 * @author Pyxis Effector Team
 * @license GPL-3.0-or-later
 */

        (function() {
            let activeImageBase64 = null;
            let activeImageName = "screenshot.png";
            let isSending = false;

            function open() {
                const modal = document.getElementById("pyxis-bug-report-modal");
                if (!modal) return;
                
                const intentEl = document.getElementById("pyxis-bug-intent");
                const failEl = document.getElementById("pyxis-bug-failure");
                if (intentEl) intentEl.value = "";
                if (failEl) failEl.value = "";
                
                clearImage();
                hideFeedback();
                
                const chkDiag = document.getElementById("pyxis-bug-chk-diag");
                if (chkDiag) chkDiag.checked = true;
                
                const logsPreview = document.getElementById("pyxis-bug-logs-preview");
                if (logsPreview) logsPreview.style.display = "none";
                
                updateLogsText();

                modal.style.display = "flex";
                
                setTimeout(function() {
                    if (intentEl) intentEl.focus();
                }, 50);

                window.addEventListener("paste", handleGlobalPaste);
            }

            function close() {
                const modal = document.getElementById("pyxis-bug-report-modal");
                if (modal) modal.style.display = "none";
                window.removeEventListener("paste", handleGlobalPaste);
            }

            function handleGlobalPaste(e) {
                const modal = document.getElementById("pyxis-bug-report-modal");
                if (!modal || modal.style.display === "none") return;
                
                const clip = e.clipboardData || (e.originalEvent && e.originalEvent.clipboardData);
                const items = clip ? clip.items : null;
                if (!items) return;

                for (let i = 0; i < items.length; i++) {
                    const item = items[i];
                    if (item.type && item.type.indexOf("image") !== -1) {
                        const blob = item.getAsFile();
                        if (blob) {
                            processImageFile(blob, "clipboard_screenshot.png");
                            e.preventDefault();
                            break;
                        }
                    }
                }
            }

            function processImageFile(file, customName) {
                if (!file || !file.type || !file.type.startsWith("image/")) {
                    showFeedback("error", "Por favor selecciona un archivo de imagen válido.");
                    return;
                }

                const objectUrl = URL.createObjectURL(file);
                const tempImg = new Image();

                tempImg.onload = function() {
                    try {
                        const canvas = document.createElement("canvas");
                        let width = tempImg.naturalWidth || tempImg.width;
                        let height = tempImg.naturalHeight || tempImg.height;

                        // Si la imagen supera 2560px, reescalar preservando proporción para máxima eficiencia
                        const maxDim = 2560;
                        if (width > maxDim || height > maxDim) {
                            if (width > height) {
                                height = Math.round((height * maxDim) / width);
                                width = maxDim;
                            } else {
                                width = Math.round((width * maxDim) / height);
                                height = maxDim;
                            }
                        }

                        canvas.width = width;
                        canvas.height = height;
                        const ctx = canvas.getContext("2d");
                        ctx.drawImage(tempImg, 0, 0, width, height);

                        // Conversión a WebP optimizado (calidad 0.85)
                        let webpDataUrl = canvas.toDataURL("image/webp", 0.85);

                        // Fallback de seguridad en caso de que el entorno no soporte exportación webp
                        if (!webpDataUrl || !webpDataUrl.startsWith("data:image/webp")) {
                            webpDataUrl = canvas.toDataURL("image/png");
                        }

                        activeImageBase64 = webpDataUrl;
                        const baseName = (customName || file.name || "screenshot").replace(/\.[^.]+$/, "");
                        activeImageName = baseName + ".webp";

                        const prompt = document.getElementById("pyxis-bug-drop-prompt");
                        const wrap = document.getElementById("pyxis-bug-preview-wrap");
                        const img = document.getElementById("pyxis-bug-preview-img");
                        const name = document.getElementById("pyxis-bug-preview-name");

                        if (img) img.src = activeImageBase64;
                        if (name) name.textContent = activeImageName;
                        if (prompt) prompt.style.display = "none";
                        if (wrap) wrap.style.display = "flex";

                        hideFeedback();
                    } catch (err) {
                        showFeedback("error", "Error al procesar la imagen: " + (err.message || String(err)));
                    } finally {
                        URL.revokeObjectURL(objectUrl);
                    }
                };

                tempImg.onerror = function() {
                    URL.revokeObjectURL(objectUrl);
                    showFeedback("error", "No se pudo cargar la imagen seleccionada.");
                };

                tempImg.src = objectUrl;
            }

            function clearImage() {
                activeImageBase64 = null;
                activeImageName = "screenshot.png";
                
                const fileInput = document.getElementById("pyxis-bug-file-input");
                if (fileInput) fileInput.value = "";
                
                const prompt = document.getElementById("pyxis-bug-drop-prompt");
                const wrap = document.getElementById("pyxis-bug-preview-wrap");
                const img = document.getElementById("pyxis-bug-preview-img");
                
                if (img) img.src = "";
                if (prompt) prompt.style.display = "flex";
                if (wrap) wrap.style.display = "none";
            }

            function toggleLogsView() {
                const preview = document.getElementById("pyxis-bug-logs-preview");
                const btnTxt = document.getElementById("pyxis-bug-logs-toggle-txt");
                if (!preview) return;

                if (preview.style.display === "none") {
                    updateLogsText();
                    preview.style.display = "block";
                    if (btnTxt && window.t) btnTxt.textContent = window.t("bug_report.hide_logs");
                } else {
                    preview.style.display = "none";
                    if (btnTxt && window.t) btnTxt.textContent = window.t("bug_report.view_logs");
                }
            }

            function updateLogsText() {
                const logsEl = document.getElementById("pyxis-bug-logs-text");
                if (!logsEl) return;
                
                const devlogs = (window.PyxisDevToolsLogs || []).slice(-40);
                let text = "--- [DevTools Logs (" + devlogs.length + " entries)] ---\n";
                text += devlogs.length > 0 ? devlogs.join("\n") : "(Sin errores recientes en DevTools)\n";
                logsEl.textContent = text;
            }

            function showFeedback(type, msg) {
                const fb = document.getElementById("pyxis-bug-feedback");
                if (!fb) return;
                fb.className = "pyxis-bug-feedback " + type;
                fb.textContent = msg;
                fb.style.display = "block";
            }

            function hideFeedback() {
                const fb = document.getElementById("pyxis-bug-feedback");
                if (fb) fb.style.display = "none";
            }

            async function send() {
                if (isSending) return;

                const intentEl = document.getElementById("pyxis-bug-intent");
                const failEl = document.getElementById("pyxis-bug-failure");
                const intent = (intentEl ? intentEl.value : "").trim();
                const failure = (failEl ? failEl.value : "").trim();

                if (!intent || !failure) {
                    const errMsg = window.t ? window.t("bug_report.error_empty") : "Por favor completa ambos campos antes de enviar.";
                    showFeedback("error", errMsg);
                    return;
                }

                const chkDiag = document.getElementById("pyxis-bug-chk-diag");
                const includeDiagnostics = chkDiag ? chkDiag.checked : true;

                isSending = true;
                const btnSend = document.getElementById("pyxis-bug-btn-send");
                const sendTxt = document.getElementById("pyxis-bug-send-txt");
                if (btnSend) btnSend.disabled = true;
                if (sendTxt && window.t) sendTxt.textContent = window.t("bug_report.sending");
                hideFeedback();

                const payload = {
                    intent: intent,
                    failure: failure,
                    image_base64: activeImageBase64,
                    include_diagnostics: includeDiagnostics,
                    devtools_logs: includeDiagnostics ? (window.PyxisDevToolsLogs || []).slice(-100) : [],
                    resolution: window.innerWidth + "x" + window.innerHeight
                };

                try {
                    let res = null;
                    if (window.pywebview && window.pywebview.api && typeof window.pywebview.api.send_bug_report === "function") {
                        res = await window.pywebview.api.send_bug_report(payload);
                    } else {
                        res = { success: false, error: "Backend API not available in standalone browser" };
                    }

                    if (res && res.success) {
                        const succMsg = window.t ? window.t("bug_report.success") : "¡Reporte enviado con éxito!";
                        showFeedback("success", succMsg);
                        setTimeout(function() {
                            close();
                        }, 2500);
                    } else {
                        const err = (res && res.error) ? res.error : "Unknown error";
                        const errFmt = window.t ? window.t("bug_report.error_send", { err: err }) : `Error al enviar: ${err}`;
                        showFeedback("error", errFmt);
                    }
                } catch(err) {
                    showFeedback("error", "Error inesperado: " + (err.message || String(err)));
                } finally {
                    isSending = false;
                    if (btnSend) btnSend.disabled = false;
                    if (sendTxt && window.t) sendTxt.textContent = window.t("bug_report.send");
                }
            }

            function setupDomEvents() {
                const dropzone = document.getElementById("pyxis-bug-dropzone");
                const fileInput = document.getElementById("pyxis-bug-file-input");

                if (dropzone && fileInput) {
                    dropzone.addEventListener("click", function(e) {
                        if (e.target.closest(".pyxis-bug-preview-del")) return;
                        fileInput.click();
                    });

                    fileInput.addEventListener("change", function(e) {
                        if (e.target.files && e.target.files[0]) {
                            processImageFile(e.target.files[0]);
                        }
                    });

                    dropzone.addEventListener("dragover", function(e) {
                        e.preventDefault();
                        dropzone.classList.add("dragover");
                    });

                    dropzone.addEventListener("dragleave", function(e) {
                        e.preventDefault();
                        dropzone.classList.remove("dragover");
                    });

                    dropzone.addEventListener("drop", function(e) {
                        e.preventDefault();
                        dropzone.classList.remove("dragover");
                        if (e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files[0]) {
                            processImageFile(e.dataTransfer.files[0]);
                        }
                    });
                }

                window.addEventListener("keydown", function(e) {
                    if (e.key === "Escape") {
                        const modal = document.getElementById("pyxis-bug-report-modal");
                        if (modal && modal.style.display !== "none") {
                            close();
                        }
                    }
                });
            }

            if (document.readyState === "loading") {
                document.addEventListener("DOMContentLoaded", setupDomEvents);
            } else {
                setupDomEvents();
            }

            window.PyxisBugReport = {
                open: open,
                close: close,
                send: send,
                clearImage: clearImage,
                toggleLogsView: toggleLogsView
            };
        })();

        /* =============================================================================
           PYXIS COMMUNITY & SOCIAL LINKS CONTROLLER
           ============================================================================= */
        (function() {
            function open() {
                const modal = document.getElementById("pyxis-community-modal");
                if (!modal) return;
                modal.classList.remove("is-open");
                void modal.offsetWidth; // Reflow to reset CSS animations
                modal.classList.add("is-open");
                modal.style.display = "flex";
                const toast = document.getElementById("pyxis-com-toast");
                if (toast) toast.style.display = "none";
            }

            function close() {
                const modal = document.getElementById("pyxis-community-modal");
                if (modal) {
                    modal.classList.remove("is-open");
                    modal.style.display = "none";
                }
            }

            function openUrl(url) {
                if (window.pywebview && window.pywebview.api && typeof window.pywebview.api.open_external_url === "function") {
                    window.pywebview.api.open_external_url(url);
                } else {
                    window.open(url, "_blank", "noopener,noreferrer");
                }
            }

            function handleLink(e, url) {
                if (e) {
                    e.preventDefault();
                    e.stopPropagation();
                }
                openUrl(url);
            }

            let toastTimer = null;
            function showToast() {
                const toast = document.getElementById("pyxis-com-toast");
                if (!toast) return;
                toast.style.display = "flex";
                if (toastTimer) clearTimeout(toastTimer);
                toastTimer = setTimeout(function() {
                    toast.style.display = "none";
                }, 3500);
            }

            function handleEmail(e) {
                if (e) {
                    e.preventDefault();
                    e.stopPropagation();
                }
                const email = "pyxiseffector@gmail.com";
                openUrl("mailto:" + email);
                if (navigator.clipboard && navigator.clipboard.writeText) {
                    navigator.clipboard.writeText(email).then(showToast).catch(showToast);
                } else {
                    showToast();
                }
            }

            function initCardInteractivity() {
                const cards = document.querySelectorAll("#pyxis-community-modal .pyxis-com-card");
                cards.forEach(function(card) {
                    card.addEventListener("mousemove", function(e) {
                        const rect = card.getBoundingClientRect();
                        const x = e.clientX - rect.left;
                        const y = e.clientY - rect.top;
                        const px = Math.max(0, Math.min(100, (x / rect.width) * 100));
                        const py = Math.max(0, Math.min(100, (y / rect.height) * 100));
                        card.style.setProperty("--card-x", px.toFixed(1) + "%");
                        card.style.setProperty("--card-y", py.toFixed(1) + "%");

                        // 3D reactive tilt (perspective 800px, max 5.5deg)
                        const rotX = ((py - 50) / 50) * -5.5;
                        const rotY = ((px - 50) / 50) * 5.5;
                        card.style.transform = "perspective(800px) rotateX(" + rotX.toFixed(2) + "deg) rotateY(" + rotY.toFixed(2) + "deg) translateY(-4px) scale(1.02)";
                    });

                    card.addEventListener("mouseleave", function() {
                        card.style.transform = "";
                        card.style.removeProperty("--card-x");
                        card.style.removeProperty("--card-y");
                    });
                });
            }

            function setupEvents() {
                const modal = document.getElementById("pyxis-community-modal");
                if (modal) {
                    modal.addEventListener("click", function(e) {
                        if (e.target === modal) {
                            close();
                        }
                    });
                }
                window.addEventListener("keydown", function(e) {
                    if (e.key === "Escape") {
                        if (modal && modal.style.display !== "none") {
                            close();
                        }
                    }
                });
                initCardInteractivity();
            }

            if (document.readyState === "loading") {
                document.addEventListener("DOMContentLoaded", setupEvents);
            } else {
                setupEvents();
            }

            window.PyxisCommunity = {
                open: open,
                close: close,
                handleLink: handleLink,
                handleEmail: handleEmail
            };
        })();
