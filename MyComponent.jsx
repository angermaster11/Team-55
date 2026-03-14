import {useState} from "react";

function MyComponent() {

    const [name, setName] = useState("");
    const [shipping, setShipping] = useState("");

    function handleNameChange(event) {
        setName(event.target.value);
    }

    const handleShippingChange = (event) => {
        setShipping(event.target.value);
    }

    return(
        <div>
            <input onChange={handleNameChange}></input>
            <p>Name : {name}</p>

            <label>
                <input name="ship" value="Pick Up" type="radio" onChange={handleShippingChange} checked={shipping === "Pick Up"}></input>
                Pick Up
            </label>
            <br></br>
            <label>
                <input name="ship" value="Delivery" type="radio" onChange={handleShippingChange} checked={shipping === "Delivery"}></input>
                Delivery
            </label>

            <p>Shipping : {shipping}</p>


        </div>
    )
}

export default MyComponent;