## PythonAnywhere integration

<p class="mermaid">
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
  click D "https://syntrillo.pythonanywhere.com" "goto syntrillo.pythonanywhere.com"
</p>
