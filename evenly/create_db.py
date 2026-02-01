import sqlite3

# Connect to the database
conn = sqlite3.connect("evenly.db")
cursor = conn.cursor()

try:
    # Add user_id 2 and 3 as members of group_id 1
    cursor.execute("INSERT OR IGNORE INTO GroupMembers (group_id, user_id) VALUES (?, ?)", (1, 2))
    cursor.execute("INSERT OR IGNORE INTO GroupMembers (group_id, user_id) VALUES (?, ?)", (1, 3))

    # Test payments for group 1 (each member makes one payment)
    test_payments = [
        (1, 1, 25.50, "Groceries"),   # User 1 pays
        (1, 2, 15.00, "Snacks"),      # User 2 pays
        (1, 3, 30.75, "Dinner")       # User 3 pays
    ]

    for payment in test_payments:
        cursor.execute(
            "INSERT INTO Payments (group_id, paid_by, amount, description) VALUES (?, ?, ?, ?)",
            payment
        )

    # Commit changes
    conn.commit()
    print("Test data inserted successfully!")

except sqlite3.Error as e:
    print("SQLite error:", e)
    conn.rollback()

finally:
    # Close the connection
    conn.close()


    <!-- <h2>Expenses</h2>
    {% if expenses %}
        <div class="expenses-list">
            {% for expense in expenses %}
                <div class="expense-item">
                    {% if expenses %}
                    <a href="{{ url_for('expense_details', expense_id=expense['payment_id']) }}" class="btn-custom">
                        {{ expense["username"] }} bought {{ expense["description"] }} for {{ expense["amount"] }} Currency
                    </a>
                    {% endif %}
                </div>
            {% endfor %}
        </div>
    {% else %}
        <p>No expenses yet.</p>
    {% endif %}  -->
