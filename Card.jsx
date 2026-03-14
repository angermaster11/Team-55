import pic from "./assets/image.png"
function Card(){
    return (
        <div className="card">
            <img className="image" src={pic} alt="profile picture"></img>
            <h1>Captain Pirate</h1>
            <p>I love to travel world on my ships</p>
        </div>
    )
}

export default Card;