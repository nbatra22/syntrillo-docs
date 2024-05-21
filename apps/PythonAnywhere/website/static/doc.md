# Doc

Incorporating Platform as a Service (PaaS) like PythonAnywhere is pivotal. It provides a seamless API integration for remote access, enabling us to connect with the Healthie Platform and Google Drive files.

Additionally, PythonAnywhere offers a convenient platform for testing and running analyses, expanding our capabilities beyond the Healthie ecosystem. The underlying code is efficiently managed on GitHub, facilitating collaborative development and streamlined deployment on PythonAnywhere.


## PythonAnywhere integration

<pre class="mermaid">
graph TD;
  A(PythonAnywhere)
  B(Other Platforms\nHealthie, Castor, ...)
  C(GitHub Repository)
  D(External Tests, Analyses,\nMonitoring, Calculations, ...)
  E(Local Development)
  F(Google Sheets ...)
  G(No code\necosystem)
  A ---|API| B
  C --->|Code Deployed| A
  C --- E
  A ----|API| F
  A ---|API| G
  A ----|syntrillo.pythonanywhere.com| D
  G ---|API| B
</pre>

PaaS such as PythonAnywhere:

   - serves as an API endpoint that can be accessed remotely from other platforms: the [Healthie Platform](#) and [Google Drive files](#).
   - offers web pages for testing your code or running specific analyses outside the Healthie platform: [https://syntrillo.pythonanywhere.com](https://syntrillo.pythonanywhere.com)

The code allowing to run these analyses is hosted on GitHub:

   - is developped on the developpers' local machines
   - is deployed to PythonAnywhere


