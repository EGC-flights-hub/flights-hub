# Diario de equipo de fligths hub

## Incidencias 

- Retraso en la implementación del WI dataset durante el M2; ha sido pospuesto para el M3.

- Las ramas de desarrollo no eran borradas tras la finalización de su tiempo de vida, además este era muy largo. Se han tomado medidas correctivas, creando ramas más atómicas y eliminando estas cuando cumplen su objetivo. Además se han documentado la norma en el Acta Fundacional ya que esta no estaba incluida en la gestión de ramas. 

- Hay ciertas vulnerabilidades y ciertos hotspots del código base de UVL cuya solución rompen el correcto funcionamiento de la aplicación. Se ha documentado la solución en el Acta Fundacinal.

- La documentación no era accesible para nadie externo al proyecto, lo que dificulta las tareas de corrección y entendimiento del proyecto. Se han pasado a .md los documentos y subido a github para solucionarlo.

- Se ha detectado con bastante retraso el mal funcionamiento del workflow Pytest. Se ha corregido inmediatamente siguiendo el procedimiento.

- Se ha notificado formalmente al compañero Samuel por su inactividad siguiendo el proceso declarado en el acta fundacional.

- Se encontró el antiguo logo de uvlhub en la página de error 404. Se corrigió inmediatamente.

- Se ha identificado un mal funcionamiento en la descarga de csv. Ha sido corregido inmediatamente.

- Se ha identificado que la badge no cumplia el requisito de actualización dinámica. Se ha corregido inmediatamente.

- Se ha añadido como incidencia (aunque fue un falso positivo) la no actualización de los despliegues de preproducción al subir cambios. Resultó ser un falso positivo pero como el equipo se mantuvo un buen rato buscando el error; queda registrado de cara al futuro.


## Decisiones de diseño

- Se ha implementado Sonarqube solo en la rama main debido a la necesidad de utilizar planes de pago para adaptarlo al workflow propuesto inicialmente.

- Dado que solo se van a utilizar CSV, eliminar todo lo referente a UVL y sobrescribirlo para CSV. Eliminación de test e implementación de featureModel, realizando un modelo mucho más simple que solo trabaja con dataset y csv.

- Se ha decidido que el "Documento del proyecto" descrito en el Acta fundacional sea el ReadMe y el contenido de este ha sido extendido.

- Se ha decidido que la badge se implemente mediante uso de SVG. Shields.io queda descargado por no poder generar badges en localhost.

- Se ha decidido crear únicamente un test de creación de nueva versión debido a que los test de selenium generados por la IDE no ofrecen la precisión necesaria y se rompen si no se replica el caso exactamente (aunque la base de datos esté exactamente igual).

- Dado que Sonarqube se implementa solo en main, y que Trivy y Dependency check ejecutan análisis sobre configuraciones y dependencias que no son algo que cambien demasiado en cada commit; se ha decidido (a partir del M2, M2 incluido) que los reportes de seguridad serían revisados ante cada Milestone.

- Como el ciclo CICD está centrado en la Seguridad más que en la mantenibilidad del código (porque este proyecto dejará de ser mantenido una vez finalizada la asignatura), los bad smells de sonarqube que salían inicialmente en el proyecto relacionados on esta; y los bad smells que sean el mismo tipo de error en nuestro códigos serán deprecados.
