# Web Subscription project

This project is a basic website based on django 5.2 that offers:
-   User accounts
-   Stripe payment of subscription
-   e-mailing
-   User registration with email confirmation
-   Login restricted to users with confirmed emails
-   User profile with additional information
-   Logging of important user events.


## Features Implemented

- Users can register for an account. After registration, a confirmation email is sent to the provided email address.
- Users must confirm their email by clicking the link in the email before they can log in.
- Only users with confirmed emails can log in and some pages are restricted the logged in users.
- User profiles store additional information, including whether the email is confirmed.
- Custom login and registration pages with user feedback.
- The user can purchase a subscription through Stripe.
- Test covering most of above have been implemented.

## Installation

python3.12 -m venv .venv
pip install django==5.2.3
pip install -r requirements.txt

## Bootstrap Setup

This project uses [Bootstrap 5.3.0](https://getbootstrap.com/) and [Bootstrap Icons 1.10.0](https://icons.getbootstrap.com/) for styling and UI components. Both are included via CDN links in the main base template (`website/accounts/templates/registration/base.html`).

- **Bootstrap CSS** and **Bootstrap JS** are loaded from the official CDN:
  - CSS: `https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css`
  - JS: `https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js`
- **Bootstrap Icons** are loaded from:
  - `https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.0/font/bootstrap-icons.css`

No local installation or npm package is required for Bootstrap or its icons. You can customize the styles further by editing the `<style>` section in the base template.

## Django functions
start server    : python manage.py runserver
test all        : python manage.py test
update database : python manage.py makemigrations
                : python manage.py migrate

# Stripe (https://dashboard.stripe.com/test/dashboard)
setup products  : https://dashboard.stripe.com/test/products?active=true
setup webhook   : https://dashboard.stripe.com/test/webhooks
setup API keys  : https://dashboard.stripe.com/test/apikeys


## Setup of ngrok for testing webhooks from local server.
Testing with stripe in the loop requirest a connection between local host and strips api.
This can be established using ngrok a service connectin from stripe to a local port on the local web sever.

Run with: ngrok http http://localhost:8080



