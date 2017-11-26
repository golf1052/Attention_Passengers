# AttentionPassengers
The next red line train to Alewife is on :fire:

[![Deploy](https://www.herokucdn.com/deploy/button.png)](https://heroku.com/deploy)

This project was originally built at [HackBeanpot 2015](http://hackbeanpot.com/) by [Sanders Lauture](https://golf1052.com), [Tevin Otieno](https://twitter.com/tevinwastaken), and [Andrew Knueven](https://twitter.com/andrewknueven). The original site is still available at [https://attentionpassengers.com/](https://attentionpassengers.com/).

The number may or may not work anymore which is why you can now try the project out by deploying to your own Heroku account.

## Setup
You'll need to set the following environment variables. These are the same ones that Heroku asks for.
- TWILIO_ACCOUNT_SID - Your Twilio account SID
- TWILIO_AUTH_TOKEN - Your Twilio auth token
- TWILIO_NUMBER - Your Twilio number
- MBTA_API_KEY - Your MBTA API key. You can use the default of `wX9NwuHnZU2ToO7GmGR9uw` but this is not recommended as it may not work. You can register for a MBTA API key [here](http://realtime.mbta.com/Portal/).

After deploying you'll be able to see the site at your Heroku url. Next you'll need to setup your Twilio number to send Messaging HTTP POST requests to your Heroku url.

Once you've done that you'll be able to message your number, something like `ruggles to dtx` and you'll get back information about the next upcoming trains and any alerts.

## Info
The project was originally connected to [Parse](http://parseplatform.org/) back when it wasn't self hosted. Parse was going to be used to manage favorites. Some of the Parse related code has been removed to make the app work without Parse but dead code may be around still.

The app is launched by [app.py](app.py). [app.py](app.py) handles requests using Flask. If a `GET` is made the website is returned. If a `POST` is made, assumedly by Twilio, then the text message is processed an a response is returned.

There are two versions of the core logic. [mbta.py](mbta.py) is the original hackathon implementation which takes in input like `ruggles inbound` or `oak grove to chinatown` and then returns which direction your train is going in, inbound or outbound, and the next three departure times. Any active alerts relevant to your station(s) would also be returned.

The second implementation, [mbta2.py](mbta2.py), improves on the first implementation by routing from the starting stop to the destination stop to allow the app to return arrival times and total transit times. This implementation was written a few months after the hackathon. You are no longer able to text `ruggles inbound` but now you're able to have the starting and destination stops be on different lines like `ruggles to central`. [mbta2.py](mbta2.py) will find which stop(s) you'll need to transfer at. The routing algorithm is located at `mbta2._try_find_transfer_chain()`. `mbta2.get_from_to_data()` then uses this data to get the schedule between the transfers to return the final trip itinerary. Implementation notes for this are available [here](https://github.com/golf1052/Attention_Passengers/commit/37c665f9fe07829031276176b6d8de6b9200733d#diff-9fa6efc8bbddd7947ca76c77a724cb6bR37).

The app is only able to route between the stops listed in [stops.json](stops.json). This file maps stop names and abbreviations to the MBTA internal stop names. The one big limitation with this is that stops with duplicate names, like St. Paul St on the B and C Green lines, are not mapped. One way around this would be using a mapping like `st paul st b` vs `st paul st c`.

## Bugs/Issues
The one known bug at the moment is that routing past Ashmont and Braintree doesn't give correct times. There are probably more bugs.

This only works for the MBTA subway right now but could be extended to work for other lines like the bus or the commuter rail.
