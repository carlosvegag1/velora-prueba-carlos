"""
Orquestador Principal: Coordina las dos fases del proceso de evaluación de candidatos.
"""

from typing import Optional
from langchain_core.language_models import BaseChatModel

from ..modelos import (
    ResultadoEvaluacion, ResultadoFase1, Requisito, TipoRequisito, RespuestaEntrevista, NivelConfianza
)
from ..nucleo import AnalizadorFase1, EntrevistadorFase2
from ..utilidades import cargar_archivo_texto, calcular_puntuacion
from ..infraestructura.llm import configurar_langsmith, obtener_cliente_langsmith


class Orquestador:
    """
    Orquestador central del sistema Velora.
    
    Fase 1: Análisis de oferta y CV (AnalizadorFase1)
    Fase 2: Entrevista conversacional con streaming (EntrevistadorFase2)
    """
    
    def __init__(
        self,
        proveedor: Optional[str] = None,
        nombre_modelo: Optional[str] = None,
        temperatura_fase1: float = 0.1,
        temperatura_fase2: float = 0.7,
        llm_fase1: Optional[BaseChatModel] = None,
        llm_fase2: Optional[BaseChatModel] = None,
        api_key: Optional[str] = None,
        habilitar_langsmith: bool = True
    ):
        """Inicializa el orquestador con componentes de Fase 1 y Fase 2."""
        self._langsmith_habilitado = False
        if habilitar_langsmith:
            langsmith = configurar_langsmith()
            self._langsmith_habilitado = langsmith is not None
        
        self._proveedor = proveedor
        self._nombre_modelo = nombre_modelo
        self._api_key = api_key
        self._ultimo_run_id: Optional[str] = None
        
        self.analizador_fase1 = AnalizadorFase1(
            llm=llm_fase1,
            proveedor=proveedor,
            nombre_modelo=nombre_modelo,
            temperatura=temperatura_fase1,
            api_key=api_key
        )
        
        self.entrevistador_fase2 = EntrevistadorFase2(
            llm=llm_fase2,
            proveedor=proveedor,
            nombre_modelo=nombre_modelo,
            temperatura=temperatura_fase2,
            api_key=api_key
        )
    
    @property
    def phase1_analyzer(self):
        return self.analizador_fase1
    
    @property
    def phase2_interviewer(self):
        return self.entrevistador_fase2
    
    def evaluar_candidato(
        self,
        ruta_oferta: Optional[str] = None,
        ruta_cv: Optional[str] = None,
        texto_oferta: Optional[str] = None,
        texto_cv: Optional[str] = None,
        interactivo: bool = True,
        respuestas_candidato: Optional[list] = None
    ) -> ResultadoEvaluacion:
        """Ejecuta la evaluación completa del candidato (Fase 1 + Fase 2 opcional)."""
        if ruta_oferta:
            oferta = cargar_archivo_texto(ruta_oferta)
        elif texto_oferta:
            oferta = texto_oferta
        else:
            raise ValueError("Debe proporcionar ruta_oferta o texto_oferta")
        
        if ruta_cv:
            cv = cargar_archivo_texto(ruta_cv)
        elif texto_cv:
            cv = texto_cv
        else:
            raise ValueError("Debe proporcionar ruta_cv o texto_cv")
        
        resultado_fase1 = self.analizador_fase1.analizar(oferta, cv)
        
        # Si descartado, no continuar a Fase 2
        if resultado_fase1.descartado:
            return ResultadoEvaluacion(
                resultado_fase1=resultado_fase1,
                fase2_completada=False,
                respuestas_entrevista=[],
                puntuacion_final=resultado_fase1.puntuacion,
                requisitos_finales_cumplidos=resultado_fase1.requisitos_cumplidos,
                requisitos_finales_no_cumplidos=resultado_fase1.requisitos_no_cumplidos,
                descartado_final=True,
                resumen_evaluacion=self._generar_resumen(resultado_fase1, [], resultado_fase1.puntuacion)
            )
        
        # Si no hay requisitos faltantes, no hay Fase 2
        if not resultado_fase1.requisitos_faltantes:
            return ResultadoEvaluacion(
                resultado_fase1=resultado_fase1,
                fase2_completada=False,
                respuestas_entrevista=[],
                puntuacion_final=resultado_fase1.puntuacion,
                requisitos_finales_cumplidos=resultado_fase1.requisitos_cumplidos,
                requisitos_finales_no_cumplidos=resultado_fase1.requisitos_no_cumplidos,
                descartado_final=False,
                resumen_evaluacion=self._generar_resumen(resultado_fase1, [], resultado_fase1.puntuacion)
            )
        
        # Modo batch: usar respuestas predefinidas
        if not interactivo and respuestas_candidato:
            respuestas_entrevista = self._realizar_entrevista_batch(
                resultado_fase1, cv, respuestas_candidato
            )
        else:
            # Modo interactivo: el frontend maneja el streaming
            return ResultadoEvaluacion(
                resultado_fase1=resultado_fase1,
                fase2_completada=False,
                respuestas_entrevista=[],
                puntuacion_final=resultado_fase1.puntuacion,
                requisitos_finales_cumplidos=resultado_fase1.requisitos_cumplidos,
                requisitos_finales_no_cumplidos=resultado_fase1.requisitos_no_cumplidos,
                descartado_final=False,
                resumen_evaluacion="Pendiente: Completar entrevista interactiva (Fase 2)"
            )
        
        resultado_final = self.reevaluar_con_entrevista(resultado_fase1, respuestas_entrevista)
        return resultado_final
    
    evaluate_candidate = evaluar_candidato
    
    def _realizar_entrevista_batch(
        self,
        resultado_fase1: ResultadoFase1,
        cv: str,
        respuestas_candidato: list
    ) -> list:
        """Realiza la entrevista en modo batch con respuestas predefinidas."""
        self.entrevistador_fase2.inicializar_entrevista(
            nombre_candidato="candidato",
            resultado_fase1=resultado_fase1,
            contexto_cv=cv
        )
        
        estado = self.entrevistador_fase2.obtener_estado()
        respuestas = []
        
        for i, req in enumerate(estado["pending_requirements"]):
            texto_respuesta = respuestas_candidato[i] if i < len(respuestas_candidato) else ""
            self.entrevistador_fase2.registrar_respuesta(i, texto_respuesta)
            
            respuestas.append(RespuestaEntrevista(
                pregunta=f"Pregunta sobre: {req['description']}",
                respuesta=texto_respuesta,
                descripcion_requisito=req['description'],
                tipo_requisito=TipoRequisito(req['type'])
            ))
        
        return respuestas
    
    def reevaluar_con_entrevista(
        self,
        resultado_fase1: ResultadoFase1,
        respuestas_entrevista: list
    ) -> ResultadoEvaluacion:
        """Re-evalúa al candidato incorporando las respuestas de la entrevista."""
        mapa_respuestas = {
            resp.descripcion_requisito: resp
            for resp in respuestas_entrevista
        }
        
        cumplidos_entrevista = []
        no_cumplidos_entrevista = []
        
        for resp in respuestas_entrevista:
            evaluacion = self.entrevistador_fase2.evaluar_respuesta(
                resp.descripcion_requisito,
                resp.tipo_requisito,
                "",
                resp.respuesta
            )
            
            requisito = Requisito(
                descripcion=resp.descripcion_requisito,
                tipo=resp.tipo_requisito,
                cumplido=evaluacion["fulfilled"],
                encontrado_en_cv=False,
                evidencia=evaluacion.get("evidence"),
                confianza=NivelConfianza(evaluacion["confidence"])
            )
            
            if evaluacion["fulfilled"]:
                cumplidos_entrevista.append(requisito)
            else:
                no_cumplidos_entrevista.append(requisito)
        
        todos_cumplidos = resultado_fase1.requisitos_cumplidos + cumplidos_entrevista
        todos_no_cumplidos = []
        
        for req in resultado_fase1.requisitos_no_cumplidos:
            if req.descripcion not in mapa_respuestas:
                todos_no_cumplidos.append(req)
        
        todos_no_cumplidos.extend(no_cumplidos_entrevista)
        
        total_requisitos = len(resultado_fase1.requisitos_cumplidos) + len(resultado_fase1.requisitos_no_cumplidos)
        cantidad_cumplidos = len(todos_cumplidos)
        tiene_obligatorio_no_cumplido = any(
            req.tipo == TipoRequisito.OBLIGATORIO and not req.cumplido
            for req in todos_no_cumplidos
        )
        
        puntuacion_final = calcular_puntuacion(total_requisitos, cantidad_cumplidos, tiene_obligatorio_no_cumplido)
        descartado_final = tiene_obligatorio_no_cumplido
        
        resumen_evaluacion = self._generar_resumen(
            resultado_fase1, respuestas_entrevista, puntuacion_final
        )
        
        return ResultadoEvaluacion(
            resultado_fase1=resultado_fase1,
            fase2_completada=True,
            respuestas_entrevista=respuestas_entrevista,
            puntuacion_final=puntuacion_final,
            requisitos_finales_cumplidos=todos_cumplidos,
            requisitos_finales_no_cumplidos=todos_no_cumplidos,
            descartado_final=descartado_final,
            resumen_evaluacion=resumen_evaluacion
        )
    
    reevaluate_with_interview = reevaluar_con_entrevista
    
    def _generar_resumen(
        self,
        resultado_fase1: ResultadoFase1,
        respuestas_entrevista: list,
        puntuacion_final: float
    ) -> str:
        """Genera un resumen ejecutivo de la evaluación."""
        partes = [
            f"Puntuación Final: {puntuacion_final:.1f}%",
            f"\nRequisitos Cumplidos: {len(resultado_fase1.requisitos_cumplidos)}",
            f"Requisitos No Cumplidos: {len(resultado_fase1.requisitos_no_cumplidos)}",
        ]
        
        if respuestas_entrevista:
            partes.append(f"\nEntrevista Realizada: {len(respuestas_entrevista)} pregunta(s)")
        
        if resultado_fase1.descartado or (puntuacion_final == 0 and any(
            req.tipo == TipoRequisito.OBLIGATORIO
            for req in resultado_fase1.requisitos_no_cumplidos
        )):
            partes.append("\nDECISIÓN: CANDIDATO DESCARTADO (requisito obligatorio no cumplido)")
        else:
            partes.append(f"\nDECISIÓN: {'APROBADO' if puntuacion_final >= 50 else 'REQUIERE REVISIÓN'}")
        
        return "\n".join(partes)
    
    def registrar_feedback(
        self,
        puntuacion: float,
        comentario: Optional[str] = None,
        run_id: Optional[str] = None
    ) -> bool:
        """Registra feedback del usuario en LangSmith para mejora continua."""
        if not self._langsmith_habilitado:
            return False
        
        target_run_id = run_id or self._ultimo_run_id
        if not target_run_id:
            return False
        
        try:
            langsmith = obtener_cliente_langsmith()
            if langsmith:
                langsmith.create_feedback(
                    run_id=target_run_id,
                    key="user_satisfaction",
                    score=puntuacion,
                    comment=comentario or ""
                )
                return True
        except Exception:
            pass
        
        return False
    
    record_feedback = registrar_feedback
    
    def obtener_estado_langsmith(self) -> dict:
        """Obtiene el estado de la integración con LangSmith."""
        return {
            "enabled": self._langsmith_habilitado,
            "last_run_id": self._ultimo_run_id,
            "client_available": obtener_cliente_langsmith() is not None
        }
    
    get_langsmith_status = obtener_estado_langsmith


CoordinadorEvaluacion = Orquestador
Orchestrator = Orquestador
CandidateEvaluator = Orquestador
