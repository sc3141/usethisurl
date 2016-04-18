"""
Templates used to render content for error responses which are hopefully more
informative than the generic.
"""

GENERIC_STATUS_TEMPLATE = """
<html>
 <head>
  <title>{code} {std_desc}</title>
 </head>
 <body>
  <h1>{code} {std_desc}</h1>
  {message}<br /><br />
 </body>
</html>
"""

NOT_FOUND_STATUS_TEMPLATE = """
<html>
 <head>
  <title>{code} {std_desc}</title>
 </head>
 <body>
  <h1>{code} {std_desc}</h1>
  <h3>The resource could not be found.</h3>
  {message}<br /><br />
 </body>
</html>
"""

