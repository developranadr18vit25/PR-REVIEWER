const mongoose=require("mongoose");

const userSchema=new mongoose.Schema({
    GithubId:Number,
    Username:String,
    Name:String,
    PublicRepoCount:Number,
    ReposUrl:String,
    Email:String
})

const currUser=mongoose.model("users" , userSchema);

module.exports={
    currUser
}