using UnityEngine;

public class BaseCaptor : BaseCondition {
    public enum CaptorType { WallFront, WallLeft, WallRight, Enemy, RedArea, FieldGate, Terminal, Exit, PathFront, PathLeft, PathRight, HasOil }; 
    // Ajout du Capteur "HasOil"
    public CaptorType captorType; // Identifie quel est le block
}