using UnityEngine;

public class BasicAction : BaseElement {
	// Advice: FYFY component aims to contain only public members (according to Entity-Component-System paradigm).
    // Ajout de l'action "DrinkOil"
    public enum ActionType { Forward, TurnLeft, TurnRight, Wait, Activate, TurnBack, DrinkOil };
    public ActionType actionType;
}