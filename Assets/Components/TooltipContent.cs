using UnityEngine.EventSystems;
using UnityEngine;
using FYFY;

public class TooltipContent : MonoBehaviour, IPointerEnterHandler, IPointerExitHandler
{
    public string text;
    private Tooltip tooltip = null;

    private bool isOver = false;

    private void Start()
    {
        GameObject tooltipGO = GameObject.Find("TooltipUI_Pointer");
        if (!tooltipGO)
        {
            GameObjectManager.unbind(gameObject);
            GameObject.Destroy(this);
        }
        else
            tooltip = tooltipGO.GetComponent<Tooltip>();
    }

    public void OnPointerEnter(PointerEventData eventData)
    {
        string formatedContent = text;
        if (text.Contains("#rustyName"))
        // Permet de faire la "TooltipContent" propre aux anciens robots (nécessite d'afficher la quantité d'essence dans le réservoir)
        {
            if (GetComponent<OilTank>().quantity >= 0)
            {   
                // On affiche le niveau d'essence du robot
                formatedContent = text.Replace("#rustyName", GetComponent<AgentEdit>().associatedScriptName + "<br>Niveau d'essence: " + GetComponent<OilTank>().quantity);
            }
            else
            {
                // On affiche que le robot a une essence infinie
                formatedContent = text.Replace("#rustyName", GetComponent<AgentEdit>().associatedScriptName + "<br>Niveau d'essence: ∞ Infini ");

            }
        }else if(text.Contains("#agentName")){
            formatedContent = text.Replace("#agentName", GetComponent<AgentEdit>().associatedScriptName);
        }
        if (text.Contains("#showOilQuantity"))  
        {
            // On affiche le niveau d'essence du jerrycan
            formatedContent = text.Replace("#showOilQuantity", ""+GetComponent<JerrycanQuantity>().quantity);
        }
        tooltip.ShowTooltip(formatedContent);
        isOver = true;
    }

    public void OnPointerExit(PointerEventData eventData)
    {
        if (tooltip != null)
        {
            tooltip.HideTooltip();
            isOver = false;
        }
    }

    public void OnDisable()
    {
        if (isOver)
        {
            tooltip.HideTooltip();
            isOver = false;
        }
    }
}
