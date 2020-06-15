# yytakehome

This is a simplistic example of a URL shortening service. The application serves content to manage submission of original URLs of varying length.  It allows a user to obtain and publish a shortened URL similar to those provided by popular URL shortening services such as [tinyurl](tinyurl.com). The service then redirects HTTP requests for a shortened URL to the original URL from which the shortened URL was generated.

This started as an exercise specified by a prospective employer. I expanded the exercise to learn about Google appengine and cloud NDB.

While not necessarily a complete example of the sophistication of my coding skills, this project was a brief example (circa 2016) of how I organize python code, and the coding practices which I consider important including tests, code documentation, and adherence to a consistent coding style.

One branch, support_iri, remains a work-in-progress.  Per its name, it endeavors to extend resource identifier support from URI to IRI.   The difference between the two classes of resource identifiers is that IRI supports an [Universal Coded Character Set](https://en.wikipedia.org/wiki/Universal_Coded_Character_Set), whereas [URI](https://en.wikipedia.org/wiki/Uniform_Resource_Identifier) supports [ASCII](https://en.wikipedia.org/wiki/ASCII).
