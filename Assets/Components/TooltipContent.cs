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
        Debug.Log("Hover element");
        if (text.Contains("#agentName"))
        {
            if (GetComponent<OilTank>().quantity >= 0)
            {
                formatedContent = text.Replace("#agentName", GetComponent<AgentEdit>().associatedScriptName + "<br>Niveau d'essence: " + GetComponent<OilTank>().quantity);
            }
            else
            {
                formatedContent = text.Replace("#agentName", GetComponent<AgentEdit>().associatedScriptName + "<br>Niveau d'essence: ∞ Infini");

            }
        }
        if (text.Contains("#showOilQuantity"))
        {
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
