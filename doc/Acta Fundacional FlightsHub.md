# Acta Fundacional

## Introducción

Este documento establece los compromisos, responsabilidades y normas que rigen el funcionamiento del grupo de trabajo durante el proyecto.

Todos los miembros se comprometen a cumplir con las disposiciones aquí descritas para asegurar un ambiente profesional orientado al éxito del proyecto.

## Objetivos del proyecto

La misión principal es la finalización de las tareas del proyecto, enfocándonos en:
    - Trabajo en equipo para producir un entregable funcional y de calidad.
    - Fomentar la colaboración, aprendizaje y transferencia de conocimiento.
    - Mantener un entorno de trabajo positivo y proactivo para superar los desafíos técnicos conjuntamente.

## Estructura del Equipo

    - Coordinador: Supervisar el progreso del proyecto, convocar y dirigir reuniones y mediar en conflictos. Inicialmente comenzará un compañero al azar y rotará conforme surjan problemas de disponibilidad para cumplirlo. 

    - Desarrollador/Tester: Rol conjunto de todos los miembros del grupo. Desarrollo de código para el cumplimiento de las funcionalidades y testeo de este.
    
    - Especialista en documentos: Encargado de mantener al día la documentación del proyecto.

## Compromisos del Miembro (Normas de Colaboración)

Todos los integrantes de flights-hub se comprometen a cumplir con las siguientes normas:

    - Puntualidad: Asistir puntualmente a todas las reuniones de planificación y seguimiento acordadas.

    - Ejecución: Participar activamente en las tareas asignadas y cumplir rigurosamente con los plazos establecidos para las issues.

    - Comunicación Proactiva: Informar al equipo de cualquier bloqueo, impedimento o riesgo de incumplimiento de plazos de manera inmediata y respetuosa.
    
    - Profesionalismo: Mantener una actitud colaborativa, constructiva y respetuosa en todas las interacciones. 
    
    - Adhesión a Políticas: Respetar de manera estricta las políticas internas de commits, ramas, issues, etc.

## Protocolo de Gestión de Discrepancias y Escalada

### Bloqueo 1: Inactividad Crónica / Falta de Participación

Situación: Un miembro no participa activamente, no asiste a reuniones o incumple repetidamente con sus responsabilidades asignadas.

Acciones:

    - Aviso Formal: Se emitirán dos avisos formales documentados en un acta de reunión.
    
    - Plazo de Rectificación: El miembro tendrá un plazo máximo de una semana para justificar su situación y demostrar una corrección inmediata en su nivel de participación.
    
    - Ajuste: El equipo intentará ajustar horarios o redefinir tareas para facilitar su reincorporación.
    
    - Sanción: Si el comportamiento persiste tras los avisos, se procederá a la discusión de su sanción o continuidad.

### Bloqueo 2: Discrepancias Técnicas o de Visión

Situación: Existe un desacuerdo fundamental sobre la implementación técnica, arquitectura o dirección estratégica del trabajo.

Acciones:


    - Diálogo Abierto: Fomentar un diálogo interno basado en argumentos técnicos y profesionales para buscar una solución de consenso.

    - Mediación: Si no se llega a un acuerdo en un plazo razonable, el Coordinador del Proyecto (o un tercero neutral) mediará en la discusión.

    - Decisión Final: Las decisiones se tomarán por consenso. Si el consenso no es viable, la decisión se resolverá mediante votación por mayoría simple del equipo.

### Bloqueo 3: Brecha de Habilidades o Disparidad de Esfuerzo

Situación: Diferencias notables en los niveles de habilidad o compromiso afectan la calidad y eficiencia del trabajo en el equipo.

Acciones:

    - Mentoría y Pairing: Los miembros con mayor experiencia ofrecerán acompañamiento y realizarán sesiones de pairing (trabajo en parejas) para transferir conocimiento y reducir la brecha de habilidades.

    - Redistribución: Si la disparidad persiste tras un aviso formal y los esfuerzos de mentoría, se reasignarán al miembro tareas de menor criticidad o se redistribuirán sus responsabilidades.
    
    - Dinámica de Grupo: Se priorizará el trabajo por parejas para fomentar el aprendizaje mutuo. En caso de dificultades mayores, el grupo completo colaborará en la resolución.

### Bloqueo 4: Caso Excepcional o No Contemplado

Acción: Se convocará una reunión urgente del equipo para discutir el escenario y decidir las medidas operativas o correctivas oportunas, documentando la decisión en acta.

Penalizaciones (Medidas Correctivas): El incumplimiento de los compromisos o la persistencia en los bloqueos resultará en la aplicación gradual de las siguientes medidas:

    - Amonestación Formal: Toda falta de compromiso o conducta inapropiada será notificada mediante una amonestación formal, la cual será documentada.

    - Aumento/Redistribución de Responsabilidades: Después de dos  amonestaciones formales, el equipo podrá decidir reasignar las tareas menos críticas del miembro afectado a otros compañeros, mientras que el miembro sancionado asume responsabilidades de documentación o soporte.
    
    - Desvinculación del Proyecto (Expulsión): Si, tras agotar todas las medidas anteriores, el miembro no logra cumplir con sus compromisos, se procederá a su expulsión definitiva del equipo. Esta decisión será tomada por consenso o votación, documentada formalmente, y las tareas restantes serán redistribuidas.

## Políticas y convenciones técnicas

### Documentación obligatoria
Los siguientes documentos deben ser actualizados de manera constante durante todo el curso del proyecto:

    - Acta fundacional: El documento presente (bases del proyecto).
    - Diario de equipo: Documento que relata las decisiones que toma el equipo durante las reuniones realizadas.
    - Documento del proyecto: Descripción del sistema desarrollado y visión global del proceso del desarrollo.

### Gestión de ramas

Se seguirá el siguiente flujo:
    
    - Main: Rama principal que contiene solo código estable, funcional y listo para producción.
    - Develop: Rama de integración. Es el cortafuegos donde converge todo el trabajo de las feature branches antes de ser probado para main.
    - Ramas feature: Ramas de nombre feature/nombre-de-feature en las cuales se desarrollan funcionalidades concretas para luego mergear con develop.
    - Ramas fix: Ramas de nombre fix/nombre-del-bug para la corrección de errores.
    - Ramas chore/style: Ramas de nombre chore/nombre-de-la-tarea para tareas de configuración, refactorización o cambios de estilo que no son nuevas funcionalidades.
    - Ramas auxiliares: para implementar correctamente los ciclos CICD. Serán nombradas cicd/nombre-de-la-implementación.
    - Ramas doc: Ramas con nombre doc o doc/documento para añadir o editar uno o varios documentos en la carpeta de documentación del proyecto.

Quedan completamente prohibidas la realización de pull request para el mergeo de código.

Las ramas seguiran una política ágil basadas en Gitflow con ramas de corta duración de vida en tiempo (pocos días), y poco volumen de trabajo, entendiendose por poco volumen, resolver 1 sola issue.

### Gestión de commits

La estructura del commit debe ser atómica y seguir el estándar Convencional Commit:
    <tipo>: <descripción breve>

La descripción deberá ser escrita también en inglés.
Tipos Válidos:

- feat: Inclusión de funcionalidades.
- fix: Corrección de errores.
- docs: Cambios en documentación.
- style: Cambios en estilo de código (formato, sintaxis, refactorización, sin cambios funcionales).
- test: Relacionado con pruebas unitarias o de integración.
- perf: Cambios para mejorar el rendimiento.
- ci: relacionado con integración continua
- cd: relacionado con despliegue continuo

Reglas de Buenas Prácticas:

- Atomicidad: Cada commit debe contener un único cambio significativo.
- Modo Imperativo: Usar modo imperativo en la descripción (ej: Fix: fixed login error).
- Cuerpo: El cuerpo del mensaje es obligatorio para explicar el motivo o la funcionalidad del cambio.
- Validación: Se deben pasar todas las pruebas locales implementadas antes de subir el commit.

### Gestión del cambio

Las issues podrán ser de 3 tipos:

- Bug: corrección de errores
- WorkItem: funcinalidad asignada a desarrollar en el proyecto
- Task: Tareas de cualquier tipo que no corresponda a ninguna de las anteriores: refactorización, documentación, despliegue, implementación continua...

Estas tendrán una plantilla subida en .github/ISSUE_TEMPLATE. Juan será el encargado inicial de crear todas las issues, cada desarrollador se encargará de autoasignarse la suya según el reparto.

### Gestión de la seguridad

En nuestro ciclo DevSecOps, no se definieron inicialmente qué cambios de seguridad deberían ser solventados. Por ello se definen los siguientes estándares para guiar al equipo a la hora de realizar dichos cambios.

    - No se deberán solucionar aquellos hotspots, bad smells o vulnerabilidades que afecten al código base del proyecto forkeado desde UVLHUB que rompa el correcto funcionamiento de FligthsHub. Se tendrán en cuenta principalmente las malas prácticas o vulnerabilidades encontradas en el código generado por nuestro equipo. 

    - Dada su dificultad por las vulnerabilidades arrastradas del código base, no se establecerá ninguna Quality Gate para el análisis de Sonarqube, aunque obviamente este se tendrá en cuenta.

    - Para realizar commits más atómicos, los commits de seguridad se realizarán bajo el nombre "fix: security report" o semejante y esto significará que ese commit arregla problemas encontrados en cualquiera de los informes generados por nuestras herramientas.

##### Esta documentación ha sido actualizada a lo largo del cuatrimestre en el drive del proyecto. Por incidencias en la sesión de seguimiento, este ha sido pasado a .md y subido a git para tener constancia de que está y subir el historial de cambios.
