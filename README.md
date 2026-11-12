# FlipLens — AI Resale Scanner

FlipLens is an AI-powered web application that helps people determine whether secondhand items are worth buying and reselling. Users upload a photo of an item, enter its purchase price, and receive an estimated resale value and potential profit based on comparable eBay listings.

## Try it

**Live App:** https://fliplens.streamlit.app/

**Demo Video:** [Add video link after recording]

**GitHub Repository:** [FlipLens on GitHub](https://github.com/PatrickWylly/FlipLens)

## How to test it

1. Open the live application using the link above.
2. Upload a clear photograph of a product, preferably with its brand or model visible.
3. Enter the price you would pay for the item.
4. Click **Analyze Item**.
5. Wait for the AI to identify the product and search eBay.
6. Review the estimated resale price, potential profit, and comparable eBay listings.
7. Try changing the purchase price to see how it affects the estimated profit.

No account or login is required to use the application.

## Track

**ML / AI**

FlipLens uses image recognition to identify physical products and combines that information with real-world marketplace data to estimate resale profitability.

## How it works

**Trigger:** The user uploads a photograph and enters a potential purchase price.

**AI Step:** Google Gemini analyzes the uploaded image and identifies the product, including its name, brand, model, category, and condition when possible.

**Marketplace Search:** The application uses the identified product information to search eBay for comparable active listings. It filters out certain irrelevant listings and prioritizes closer matches.

**Output:** FlipLens displays the identified product, estimated resale value, potential profit, and comparable eBay listings with images, prices, and links.

The estimated resale value is calculated using the median asking price of the filtered listings. Estimated profit subtracts the user's purchase price, an assumed 13% marketplace fee, and $8 in shipping costs.

## Superpowers / Integrations

- **Real-World data:** Retrieves comparable marketplace listings, prices, product images, and links from the *eBay Browse API.*
- **Vision** Analyzes photographs and identifies products without requiring the user to manually search for them using *Google Gemini Vision.*

## Why it matters to me

I wanted to build an AI application that solves a practical, everyday problem. I love thrifting and finding good deals on junk at flea markets and garage sales. In highschool I started reselling equipment that I purchased at garage sales. This tool will help me with that greatly, allowing me to move a little smoother through flea market tables and goodwill shelves.

## Built with

- **Python** — Application logic and profit calculations
- **Google Gemini 3.5 Flash-Lite** — AI image recognition and product identification
- **Google Gen AI SDK** — Gemini API integration
- **eBay Browse API** — Marketplace listing data
- **Streamlit** — User interface and web hosting
- **Pillow** — Image preprocessing
- **Requests** — API communication
- **Git and GitHub** — Version control and source code hosting
- **ChatGPT (OpenAI)** — AI-assisted development, code generation, debugging, and application design.

## Built by

**Patrick Wylly**

Computer Science Student at Penn State University

Developed for the **Nittany AI Student Alliance Machine Learning Bootcamp**.