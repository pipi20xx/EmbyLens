import json
import asyncio
from typing import List
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from app.db.session import get_db
from app.models.terminal import TerminalHost, QuickCommand
from app.schemas.terminal import TerminalHostCreate, TerminalHostRead, QuickCommandCreate, QuickCommandRead
from app.services.terminal_service import TerminalService
from app.utils.logger import logger

router = APIRouter()

# --- 主机管理 ---

@router.get("/hosts", response_model=List[TerminalHostRead])
async def get_hosts(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(TerminalHost))
    return result.scalars().all()

@router.post("/hosts", response_model=TerminalHostRead)
async def create_host(host: TerminalHostCreate, db: AsyncSession = Depends(get_db)):
    new_host = TerminalHost(**host.dict())
    db.add(new_host)
    await db.commit()
    await db.refresh(new_host)
    return new_host

@router.put("/hosts/{host_id}", response_model=TerminalHostRead)
async def update_host(host_id: int, host: TerminalHostCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(TerminalHost).where(TerminalHost.id == host_id))
    db_host = result.scalar_one_or_none()
    if not db_host:
        raise HTTPException(status_code=404, detail="Host not found")
    for key, value in host.dict().items():
        setattr(db_host, key, value)
    await db.commit()
    await db.refresh(db_host)
    return db_host

@router.delete("/hosts/{host_id}")
async def delete_host(host_id: int, db: AsyncSession = Depends(get_db)):
    await db.execute(delete(TerminalHost).where(TerminalHost.id == host_id))
    await db.commit()
    return {"status": "success"}

# --- 快速命令 ---

@router.get("/commands", response_model=List[QuickCommandRead])
async def get_commands(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(QuickCommand).order_by(QuickCommand.sort_order.asc(), QuickCommand.id.desc()))
    return result.scalars().all()

@router.post("/commands/reorder")
async def reorder_commands(ids: List[int] = Body(...), db: AsyncSession = Depends(get_db)):
    for index, cmd_id in enumerate(ids):
        await db.execute(
            delete(QuickCommand).where(QuickCommand.id == -1) # dummy to use db
        )
        # Use a more direct update
        from sqlalchemy import update
        await db.execute(
            update(QuickCommand).where(QuickCommand.id == cmd_id).values(sort_order=index)
        )
    await db.commit()
    return {"status": "success"}

@router.post("/commands", response_model=QuickCommandRead)
async def create_command(cmd: QuickCommandCreate, db: AsyncSession = Depends(get_db)):
    new_cmd = QuickCommand(**cmd.dict())
    db.add(new_cmd)
    await db.commit()
    await db.refresh(new_cmd)
    return new_cmd

@router.put("/commands/{cmd_id}", response_model=QuickCommandRead)
async def update_command(cmd_id: int, cmd: QuickCommandCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(QuickCommand).where(QuickCommand.id == cmd_id))
    db_cmd = result.scalar_one_or_none()
    if not db_cmd:
        raise HTTPException(status_code=404, detail="Command not found")
    for key, value in cmd.dict().items():
        setattr(db_cmd, key, value)
    await db.commit()
    await db.refresh(db_cmd)
    return db_cmd

@router.delete("/commands/{cmd_id}")
async def delete_command(cmd_id: int, db: AsyncSession = Depends(get_db)):
    await db.execute(delete(QuickCommand).where(QuickCommand.id == cmd_id))
    await db.commit()
    return {"status": "success"}

# --- WebSocket 终端连接 ---

@router.websocket("/ws/{host_id}")
async def terminal_websocket(websocket: WebSocket, host_id: int, db: AsyncSession = Depends(get_db)):
    await websocket.accept()
    
    term_service = TerminalService()
    
    try:
        if host_id == 0:
            # 连接本机
            term_service.open_terminal()
        else:
            # 连接远程主机
            result = await db.execute(select(TerminalHost).where(TerminalHost.id == host_id))
            host_info = result.scalar_one_or_none()
            if not host_info:
                await websocket.send_text("\r\n\x1b[31m[Error] Host not found.\x1b[0m\r\n")
                await websocket.close()
                return
            
            # 将模型转为字典供服务使用
            host_dict = {
                "host": host_info.host,
                "port": host_info.port,
                "username": host_info.username,
                "auth_type": host_info.auth_type,
                "password": host_info.password,
                "private_key": host_info.private_key
            }
            await term_service.connect_ssh(host_dict)

        # 异步读取输出
        async def read_from_pty():
            try:
                while True:
                    output = term_service.read_output()
                    if output:
                        await websocket.send_text(output.decode('utf-8', errors='ignore'))
                    await asyncio.sleep(0.01)
            except Exception as e:
                logger.error(f"[Terminal] Read error: {e}")

        read_task = asyncio.create_task(read_from_pty())
        
        while True:
            message = await websocket.receive_text()
            if message.startswith('{') and 'type' in message:
                try:
                    msg = json.loads(message)
                    if msg.get("type") == "resize":
                        term_service.resize(msg.get("rows", 24), msg.get("cols", 80))
                        continue
                except: pass
            
            term_service.write_input(message)
            
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"[Terminal] WS error: {e}")
    finally:
        if 'read_task' in locals():
            read_task.cancel()
        term_service.close()