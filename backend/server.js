const express=require("express")
const app=express()
const cors=require("cors")
const authRouter=require("../backend/routes/auth_routes")

app.use(cors())

app.get("/" , (req,res)=>{
    res.send("Express is working")
})

app.use("/auth" , authRouter);

app.listen(4000,()=>{
    console.log("Running on port 4000")
})