// main.js — students will add JavaScript here as features are built

// ------------------------------------------------------------------ //
// "Get started" video modal                                          //
// ------------------------------------------------------------------ //

(function () {
    var VIDEO_EMBED_URL =
        "https://www.youtube.com/embed/-Lt-ntUDj-g?list=PLKnIA16_RmvaYH3poI0oJvbDF4zEvpq8W&index=4&autoplay=1&rel=0";

    var getStartedBtn = document.getElementById("getStartedBtn");
    var videoModal = document.getElementById("videoModal");
    var videoModalOverlay = document.getElementById("videoModalOverlay");
    var videoModalClose = document.getElementById("videoModalClose");
    var videoModalIframe = document.getElementById("videoModalIframe");

    if (!getStartedBtn || !videoModal || !videoModalIframe) {
        return;
    }

    function openVideoModal(event) {
        event.preventDefault();
        // Setting src only when opening means the video never loads
        // (or plays) until the user actually asks for it.
        videoModalIframe.src = VIDEO_EMBED_URL;
        videoModal.classList.add("is-open");
        videoModal.setAttribute("aria-hidden", "false");
        document.body.classList.add("modal-open");
    }

    function closeVideoModal() {
        videoModal.classList.remove("is-open");
        videoModal.setAttribute("aria-hidden", "true");
        document.body.classList.remove("modal-open");
        // Clearing the src (rather than just hiding the modal) stops
        // playback immediately instead of letting it continue in the background.
        videoModalIframe.src = "";
    }

    getStartedBtn.addEventListener("click", openVideoModal);
    videoModalClose.addEventListener("click", closeVideoModal);
    videoModalOverlay.addEventListener("click", closeVideoModal);

    document.addEventListener("keydown", function (event) {
        if (event.key === "Escape" && videoModal.classList.contains("is-open")) {
            closeVideoModal();
        }
    });
})();
