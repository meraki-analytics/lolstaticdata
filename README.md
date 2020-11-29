# League of Legends Static Data

This repository provides code to generate accurate champion and item data. First, a big thanks goes out to the people who work hard to maintain the League of Legends Wiki. We pull champion ability information from them because it is the only accurate source of champion data.

If you use this data, please give a shoutout to the League of Legends Wiki and to us (Meraki).

## Goals of the Project

Until now, accurate champion data that developers can use to create apps has not been reliably available. Our goal is to provide high quality champion and item data so that you can create awesome applications.

Currently, Riot's Data Dragon JSON provides champion, item, and rune info, but it can be inaccurate. In particular, champion abilities are unparsable and often have incorrect numbers. The Community Dragon project is a player-driven community that unpacks the LoL game files and is meant to augment the data that Riot provides to developers. Like DDragon, CDragon provides JSON data for champions, items, and runes; however, the champion abilities are incredibly complex and cryptic because the game requires very nuanced descriptions of the champion abilities.

In this project, we aim to strike a balance between data that is accurate and simple enough to be understandable and parsable. Having accurate data for champion abilities in particular will open up a new use-case for League of Legends apps by allowing ability damages to be calculated accurately. For example, this data may allow for quick and automated calculations of a champion's power from one patch to another (you'll need to keep track of the changes). This has never before been possible due to the inaccuracy of the available data and, therefore, the manual work required to update that data each patch.

Data other than that for champions and items should be covered by the data that Riot provides, or by the CDragon project.

Note that it is impossible to represent the enormous complexity of League of Legends data in a simple JSON format, so special cases exist that need to be handled on a case-by-case basis. This is left up to you, as the developer, to create the complex interactions that are needed by your app.

## Running the Code

```
git clone https://github.com/meraki-analytics/lolstaticdata.git
cd lolstaticdata
pip install -r requirements.txt
python -m lolstaticdata.champions # to run the champion-pulling code
python -m lolstaticdata.items     # to run the item-pulling code
```

## Contributing

The best way to contribute is to fork this repository and create a Pull Request (PR). When you create a PR, it is _crucial_ that you are extremely careful that only champions/items that you intend to affect are affected. Because the parsing of this data is so nuanced, it is easy to write code that affects more than you originally intended. So be careful, and let us know in the PR exactly what is and what is not affected by your changes. This will make the PR review go much faster.

Because this is a community resource, the code and data needs to have a particularly high standard before merging. This means we will likely be picky about syntax and about following Python's PEP 8 standard. This keeps the code and data highly readable, which is extremely important for open source software.

## Accessing the Data

In addition to providing this code, we run it and serve the resulting JSON data at http://cdn.merakianalytics.com/riot/lol/resources/latest/en-US/champions and http://cdn.merakianalytics.com/riot/lol/resources/latest/en-US/items. All champion and item data is combined, respectively, into a single file at http://cdn.merakianalytics.com/riot/lol/resources/latest/en-US/champions.json and http://cdn.merakianalytics.com/riot/lol/resources/latest/en-US/items.json

Our CDN should be up 24/7, and although we can't make any promises, it's been online and serving patch data for years without going down. Providing this data has resulted in a huge increase in data consumption, so please use this data responsibly. **If you use this data for your apps, cache it on your own servers/apps to reduce the load on our services, which will help keep it up for everyone to use.**
