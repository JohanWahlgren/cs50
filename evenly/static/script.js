function createCoin() {
    const coin = document.createElement("div");
    coin.classList.add("coin");
    document.body.appendChild(coin);

    const startPosX = Math.random() * window.innerWidth;
    coin.style.left = `${startPosX}px`;
    coin.style.animationDuration = `${3 + Math.random() * 2}s`;

    setTimeout(() => {
        coin.remove();
    }, 5000);
}

setInterval(createCoin, 500);


window.onload = function() {
    // Check if error message exists in the session
    var errorMessage = document.getElementById("errorMessage").innerText.trim();

    // If there's an error message, show the error modal
    if (errorMessage && errorMessage !== "None") {
        var errorModal = new bootstrap.Modal(document.getElementById('errorModal'));
        errorModal.show();

        // Clear the error from the session after showing the modal
        fetch("/clear_error").then(function(response) {
            if (response.ok) {
                // Optionally, you could refresh the page to ensure error is cleared
                // window.location.reload();
            }
        });
    }

    // Show the register modal if it's present
    if (document.getElementById('registerModal')) {
        var registerModal = new bootstrap.Modal(document.getElementById('registerModal'));
        //registerModal.show();
    }

    // Show the login modal if it's present
    if (document.getElementById('loginModal')) {
        var registerModal = new bootstrap.Modal(document.getElementById('loginModal'));
        //registerModal.show();
    }
};

document.addEventListener("DOMContentLoaded", function () {
    // Select all members checkbox logic
    const selectAllCheckbox = document.getElementById("select-all");
    if (selectAllCheckbox) {
        const memberCheckboxes = document.querySelectorAll("input[name='split_with']");

        selectAllCheckbox.addEventListener("change", function () {
            memberCheckboxes.forEach(checkbox => checkbox.checked = selectAllCheckbox.checked);
        });
    }

    // Expense click event to open modal
    const expenses = document.querySelectorAll(".expense-item");

    expenses.forEach(expense => {
        expense.addEventListener("click", function () {
            const expenseId = this.getAttribute("data-expense-id");

            fetch(`/expense-detail/${expenseId}`)
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        alert(data.error);
                        return;
                    }

                    // Populate modal with data
                    document.getElementById("expense-description").innerText = data.description;
                    document.getElementById("expense-amount").innerText = data.amount;
                    document.getElementById("expense-paid-by").innerText = data.paid_by;
                    document.getElementById("expense-date").innerText = data.timestamp;

                    // Populate split details
                    const splitList = document.getElementById("split-details");
                    splitList.innerHTML = ""; // Clear old data
                    data.splitters.forEach(splitter => {
                        const listItem = document.createElement("li");
                        listItem.textContent = `${splitter.username} owes ${splitter.share}`;
                        splitList.appendChild(listItem);
                    });

                    // Show the modal
                    const expenseModal = new bootstrap.Modal(document.getElementById("expenseDetailModal"));
                    expenseModal.show();
                })
                .catch(error => console.error("Error fetching expense details:", error));
        });
    });

    document.querySelectorAll(".btn-settle").forEach(button => {
        button.addEventListener("click", function () {
            const settlementId = this.getAttribute("data-settlement-id");

            fetch(`/settle-debt/${settlementId}`, { method: "POST" })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        location.reload();
                    } else {
                        alert(data.error);
                    }
                })
                .catch(error => console.error("Error:", error));
        });
    });
});
