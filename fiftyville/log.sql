-- To find out more about the crime
SELECT description, id FROM crime_scene_reports WHERE year = 2023 AND month = 7 AND day = 28 AND street = 'Humphrey Street';
-- Found out it took place at 10:15 at the bakery, and littering 16:36

-- To see what happened at the bakery at 10:15
SELECT activity, hour, minute FROM bakery_security_logs WHERE year = 2023 AND month = 7 AND day = 28;
-- Found out entry logged 10:14, exit 10:16, the thief?

--Added license plate
SELECT activity, license_plate, hour, minute FROM bakery_security_logs WHERE year = 2023 AND month = 7 AND day = 28 AND hour = 10;
-- Car with plate 5P2BI95 left at 10:16, hmm

-- Find out more from the interviews
SELECT name, transcript FROM interviews WHERE year = 2023 AND month = 7 AND day = 28;
-- The thief has a german accent, got in and drove away within 10 min of the theft, Was on ATM Legget Street earlier in the day,
-- made a phone call after leaving the bakery lasting less than a minute about taking the earliest flight tomorrow, accompliance purchase ticket.

-- See if there is a match
SELECT name FROM people WHERE license_plate IN
   (SELECT license_plate FROM bakery_security_logs WHERE year = 2023 AND month = 7 AND day = 28 AND hour = 10 AND minute > 15 AND minute < 25)
   AND phone_number IN(SELECT caller FROM phone_calls WHERE year = 2023 AND month = 7 AND day = 28 AND dura
tion < 60);
-- Answer comes out to Sofia, Diana, Kelsey, Bruce.

-- Have to narrow it down further
SELECT name FROM people WHERE id IN
   (SELECT person_id FROM bank_accounts WHERE account_number IN
      (SELECT account_number FROM atm_transactions WHERE atm_location = 'Leggett Street' AND year = 2023 AND month = 7 AND day = 28
      AND transaction_type = 'withdraw'));
-- Bruce and Diana appers on this list to

-- Check the earliest flights out of fiftyville the day after
SELECT destination_airport_id, id FROM flights WHERE origin_airport_id =
   (SELECT id FROM airports WHERE city = 'Fiftyville') AND year = 2023 AND month = 7 AND day = 29 ORDER BY flights.hour, flights.minute;
-- Earliest flight that day had destination_airport_id = 4 and id 36

-- Check the passengers
SELECT name FROM people WHERE passport_number IN(SELECT passport_number FROM passengers WHERE flight_id = 36);
-- Only Bruce appears in everything therefore Bruce is the thief

-- Where they went
SELECT city, full_name FROM airports WHERE id = 4;
-- LaGuardia Airport, New York City

-- Fund out who bruce called, find out bruces phone number
SELECT phone_number FROM people WHERE name = 'Bruce';
-- His nr is (367) 555-5533

SELECT name FROM people WHERE phone_number = (SELECT receiver FROM phone_calls WHERE caller = '(367) 555-5533'
   AND year = 2023 AND month = 7 AND day = 28);
-- His name is Robin





