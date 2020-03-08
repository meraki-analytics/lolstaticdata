# League of Legends Static Data

## Goals of the Project

#### Current Term Goals

We aim to provide the League of Legends developer community with accurate champion, item, and rune data. Other information should be covered by data that Riot provides, or by the CDragon project.

Currently, Riot's Data Dragon JSON provides champion, item, and rune info, but it can be inaccurate. In particular, champion abilities are unparsable and often have incorrect numbers.  The Community Dragon project is a player-driven community that unpacks the LoL game files and is meant to augment Riot's data. Like DDragon, CDragon provides JSON data for champions, items, and runes; however, the champion abilities are incredibly complex and cryptic because the game requires very nuanced descriptions of the champion abilities.

In this project, we provide data that is both accurate and simple enough to be understandable and parsable. Having accurate data for champion abilities in particular will open up a new use-case for League of Legends apps by allowing ability damages to be calculated accurately. For example, this data may allow for quick and automated calculations of a champion's power from one patch to another. This has never before been possible due to the inaccuracy of the available data and, therefore, the manual work required to update that data each patch.

It is impossible to represent the enormous complexity of League of Legends data in a simple JSON format, so special cases exist that need to be handled on a case-by-case basis.


#### Long Term Goals

In the long term, we hope this data will become a community resource for developers.

The goal is for this data to be the "gold standard" of League of Legends data for developers, where the complexity finds some middle ground between accurate and usable data.

This goal likely requires that data be pulled in from different sources, e.g. DDragon, CDragon, and other sources.


#### Not Finished

* We don't yet have rune data, in part because the DDragon and CDragon rune data (together) is quite good.
* A merge strategy that combines data from multiple sources needs to be implemented to provide a standard interface for merging that data.
* Time-dependent data, ideally that correlates with patch updates, would be great to have. It may be impossible to have perfect data at the beginning of each patch because some manual updates are required, but our goal is to provide nightly releases of this repository's data so that developers can access past data. If you would like to contribute to this, we need a layout for how this would all work. Just thinking through and describing this process would be a great help.
* Errors in parsing need to be identified and fixed.
* Missing data that developers want needs to be identified and added.
* Provide some way to manually edit data by contributing to this repository. In other words, we could have another community-driven data source that we pull data from.


## Contributing

The best way to contribute is to fork this repository and create a Pull Request. When creating pull requests, make sure that the data in the repository was created by the code that is in the repository (i.e. the data is up to date with the code). This will help us evaluate changes.

Because this is a community resource, the code and data needs to have a particularly high standard before merging. This means we will likely be picky about syntax and about following Python's PEP 8 standard. This keeps the code and data highly readable, which is extremely important for open source software.


## Apps Using This Data

Please create a Pull Request for this README if you would like your app added to this list. It is both an advertisement for yourself and for this project.

* We are planning to create a build calculator that will calculate champion ability damages, but it isn't finished yet.
