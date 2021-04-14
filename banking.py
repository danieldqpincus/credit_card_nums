import random
import sqlite3

conn = sqlite3.connect("card.s3db")
cur = conn.cursor()

START_MENU = "1. Create an account\n2. Log into account\n0. Exit"
BALANCE_MENU = "1. Balance \n2. Add income\n3. Do transfer\n4. Close account\n5. Log out\n0. Exit"

CREATE_CARD_TABLE = """CREATE TABLE IF NOT EXISTS card(
                        id INTEGER,
                        number TEXT UNIQUE,
                        pin TEXT,
                        balance INTEGER);"""


cur.execute(CREATE_CARD_TABLE)
conn.commit()
card_dictionary = {}


def pin_generator():
    """generates a random PIN to use in generate_and_add_card_num"""
    digit_1 = str(random.randint(0, 9))
    digit_2 = str(random.randint(0, 9))
    digit_3 = str(random.randint(0, 9))
    digit_4 = str(random.randint(0, 9))
    pin_num = digit_1 + digit_2 + digit_3 + digit_4
    return pin_num


def get_new_card_number():
    """add to the card dictionary where key = card_number and value = PIN"""
    while True:
        card_to_add = str(random.randrange(400000000000000, 400000999999999))

        # check if the new card equals any of the old cards
        for card in card_dictionary.keys():
            if card == card_to_add:
                break

        # luhn algorithm
        split_card = [int(x) for x in card_to_add]
        total_sum = 0

        for i in range(len(split_card)):
            if i % 2 == 0:
                split_card[i] *= 2

        for i in range(len(split_card)):
            if split_card[i] > 9:
                split_card[i] = split_card[i] - 9

        for num in split_card:
            total_sum += num

        if total_sum % 10 == 0:
            check_sum = 0
        else:
            check_sum = 10 - (total_sum % 10)

        card_to_add += str(check_sum)

        # add to card dictionary
        card_dictionary[card_to_add] = pin_generator()

        # add to card.s3db

        last_ids = cur.execute("SELECT * FROM card").fetchall()
        if last_ids:
            last_id = last_ids[len(last_ids) - 1].__getitem__(0)
            last_id += 1
        else:
            last_id = 0
        cur.execute("INSERT INTO card (id, number, pin, balance) VALUES (?,?,?,?)", (last_id, card_to_add, card_dictionary[card_to_add], 0))

        conn.commit()

        return card_to_add


def create_account():
    """Prints 'create new account', and adds account to working dictionary"""
    card_num = get_new_card_number()
    print("Your card has been created\nYour card number:")
    print(card_num)
    print("Your card PIN:")
    print(card_dictionary[card_num])


def add_income(card_num, amount):
    cur.execute("UPDATE card SET balance = balance + ? WHERE number = ?", (amount, card_num))
    conn.commit()


def luhn_algo_check(card_num):
    """Return True if card_num passes luhn algorithm, False if not"""

    split_card = [int(x) for x in card_num]
    check_sum_to_compare = split_card.pop()
    total_sum = 0

    for i in range(len(split_card)):
        if i % 2 == 0:
            split_card[i] *= 2

    for i in range(len(split_card)):
        if split_card[i] > 9:
            split_card[i] = split_card[i] - 9

    for num in split_card:
        total_sum += num

    if total_sum % 10 == 0:
        check_sum = 0
    else:
        check_sum = 10 - (total_sum % 10)

    if check_sum == check_sum_to_compare:
        return True
    else:
        return False


def close_account(account_num):
    cur.execute("DELETE FROM card WHERE number = ?", (account_num,))
    conn.commit()
    print("Account closed")


def login():
    card_num = input("Enter your card number:")
    card_pin = input("Enter your PIN:")
    card_check = cur.execute("""SELECT number FROM card""").fetchall()
    for card in card_check:
        if str(card.__getitem__(0)) == card_num:
            pin_check = cur.execute("""SELECT pin FROM card WHERE number = ?""", (card_num,)).fetchall()[0].__getitem__(0)

    successful_login = False

    for card in card_check:
        if str(card.__getitem__(0)) == card_num and str(pin_check) == card_pin:
            print("You have successfully logged in!")
            successful_login = True

    if successful_login is False:
        print("Wrong credentials")

    while successful_login:
        print(BALANCE_MENU)
        user_login_selection = input()
        if user_login_selection == "1":
            balance = cur.execute("SELECT balance FROM card WHERE number = ?", (card_num,)).fetchall()[0].__getitem__(0)
            print(balance)
            break
        elif user_login_selection == "2":
            amount = input("How much do you want to add? ")
            add_income(card_num, amount)
        elif user_login_selection == "3":
            receiving_card = input("What card do you want to send the amount to?")
            if int(receiving_card) > 4000009999999999 or int(receiving_card) < 4000000000000000:
                print("Such a card does not exist")
                continue
            elif not luhn_algo_check(receiving_card):
                print("Probably a mistake in the card number. Please try again!")
                continue

            sending_card_balance = int(cur.execute("SELECT balance FROM card WHERE number = ?", (card_num,)).fetchall()[0].__getitem__(0))

            amount = int(input("How much do you want to send? "))

            if sending_card_balance < amount:
                print("Not enough money!")
                continue

            if sending_card_balance >= amount and sending_card_balance > 0:
                cur.execute("UPDATE card SET balance = balance - ? WHERE number = ?", (amount, card_num))
                cur.execute("UPDATE card SET balance = balance + ? WHERE number = ?", (amount, receiving_card))

            conn.commit()

        elif user_login_selection == "4":
            close_account(card_num)
            break
        elif user_login_selection == "5":
            print("You have successfully logged out!")
            break
        else:
            exit()


conn.commit()


def main():
    while True:
        print(START_MENU)
        user_selection = input()
        if user_selection == "0":
            break
        elif user_selection == "1":
            create_account()
            conn.commit()
        elif user_selection == "2":
            login()


main()

conn.close()

