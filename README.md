# Web Subscription project

This project is a basic website based on django 5.2 that offers:
-   User accounts
-   Stripe payment of subscription
-   e-mailing
-   User registration with email confirmation
-   Login restricted to users with confirmed emails
-   User profile with additional information

## Features Implemented

- Users can register for an account. After registration, a confirmation email is sent to the provided email address.
- Users must confirm their email by clicking the link in the email before they can log in.
- Only users with confirmed emails can log in.
- User profiles store additional information, including whether the email is confirmed.
- Custom login and registration pages with user feedback.

## Installation

python3.12 -m venv .venv
pip install django==5.2.3

## Start Django Project


