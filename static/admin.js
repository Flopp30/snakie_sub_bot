document.addEventListener("DOMContentLoaded", function () {
    refundModalProcess();
    sendMessageModalProcess();
});

function refundModalProcess() {
    let modal = document.getElementById("modal-refund");
    let openBtns = document.querySelectorAll(".refund-btn");
    let closeBtns = modal.querySelectorAll(".close");
    let form = modal.querySelector('#refund-form');
    let paymentInput = form.querySelector('input[name="payment_id"]');
    openBtns.forEach((btn) => {
        btn.onclick = function () {
            paymentInput.value = this.getAttribute("paymentId");
            modal.classList.add('show');
        };
    });
    closeBtns.forEach((span) => {
        span.onclick = function () {
            closeModal(modal, [paymentInput]);
        };
    });
    document.addEventListener("keydown", function (event) {
        if (event.key === "Escape") {
            closeModal(modal, [paymentInput]);
        }
    });

    window.onclick = function (event) {
        if (event.target === modal) {
            closeModal(modal, [paymentInput]);
        }
    };
}

function closeModal(modal, inputs) {
    modal.classList.remove('show');
    inputs.forEach((input) => {
        input.value = '';
    });
}

function sendMessageModalProcess() {
    let modal = document.getElementById("modal-send-message");
    let openBtns = document.querySelectorAll(".send-msg-btn");
    let closeBtns = modal.querySelectorAll(".close");
    let form = modal.querySelector('#send-message-form');
    let withKeyboard = form.querySelector('#id_with_keyboard_container');
    form.querySelector("#id_to_users").addEventListener("change", function (event) {
        if (event.target.value === "all_unsub") {
            withKeyboard.classList.remove("hidden");
        } else {
            withKeyboard.classList.add("hidden");
        }
    });
    let userInput = form.querySelector('input[name="user_id"]');
    openBtns.forEach((btn) => {
        btn.onclick = function () {
            userInput.value = this.getAttribute("userId");
            modal.classList.add('show');
        };
    });
    closeBtns.forEach((span) => {
        span.onclick = function () {
            closeModal(modal, [userInput]);
        };
    });
    document.addEventListener("keydown", function (event) {
        if (event.key === "Escape") {
            closeModal(modal, [userInput]);
        }
    });

    window.onclick = function (event) {
        if (event.target === modal) {
            closeModal(modal, [userInput]);
        }
    };
}
