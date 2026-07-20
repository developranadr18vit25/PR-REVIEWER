const mongoose=require("mongoose");

const userSchema=new mongoose.Schema({
    GithubId:String,
    Username:String,
    Email:String,
    AccessToken:String
})

const currUser=mongoose.model("users" , userSchema);

module.exports={
    currUser
}